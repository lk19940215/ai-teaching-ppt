"""
PPTX 写回器

将修改指令 (SlideModification) 应用到原始 PPTX 文件，
在 Run 级别替换文本以保留所有格式属性。

技术文档: docs/technical-spec.md §5.4, §8

核心算法: _replace_text_preserve_format
  - 按段落分配新文本到已有段落
  - 在每个段落内替换第一个 Run 的文本、清空后续 Run
  - 所有格式属性 (字体、颜色、大小) 来自原始 Run，不做修改
"""

import logging
from pathlib import Path
from uuid import uuid4

from pptx import Presentation
from pptx.oxml.ns import qn

from .models import SlideModification, TextModification, TableCellModification, SlideSelector

logger = logging.getLogger(__name__)


class PPTXWriter:
    """PPTX 写回器：原始 PPTX + 修改指令 → 新 PPTX 文件"""

    def apply(
        self,
        source_path: Path,
        modifications: list[SlideModification],
        output_dir: Path,
    ) -> Path:
        """
        应用修改到原始 PPTX，保存为新文件。

        Args:
            source_path: 原始 PPTX 文件路径
            modifications: 修改指令列表
            output_dir: 输出目录

        Returns:
            新 PPTX 文件路径
        """
        prs = Presentation(str(source_path))
        total_applied = 0
        total_skipped = 0

        for slide_mod in modifications:
            if slide_mod.slide_index >= len(prs.slides):
                logger.warning(
                    f"slide_index {slide_mod.slide_index} 超出范围 "
                    f"(共 {len(prs.slides)} 页), 跳过"
                )
                continue

            slide = prs.slides[slide_mod.slide_index]
            shapes = list(slide.shapes)

            for text_mod in slide_mod.text_modifications:
                applied = self._apply_text_modification(shapes, text_mod, slide_mod.slide_index)
                if applied:
                    total_applied += 1
                else:
                    total_skipped += 1

            for table_mod in slide_mod.table_modifications:
                applied = self._apply_table_modification(shapes, table_mod, slide_mod.slide_index)
                if applied:
                    total_applied += 1
                else:
                    total_skipped += 1

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"modified_{uuid4().hex[:8]}.pptx"
        prs.save(str(output_path))

        logger.info(
            f"写回完成: {output_path.name}, "
            f"应用 {total_applied} 项修改, 跳过 {total_skipped} 项"
        )
        return output_path

    def _apply_text_modification(
        self, shapes: list, mod: TextModification, slide_idx: int
    ) -> bool:
        """应用单个文本修改"""
        if mod.shape_index >= len(shapes):
            logger.warning(
                f"第{slide_idx}页 shape_index {mod.shape_index} 超出范围 "
                f"(共 {len(shapes)} 个 shape), 跳过"
            )
            return False

        shape = shapes[mod.shape_index]

        if not shape.has_text_frame:
            logger.warning(
                f"第{slide_idx}页 shape_index {mod.shape_index} 不是文本框, 跳过"
            )
            return False

        current_text = shape.text_frame.text.strip()
        expected = mod.original_text.strip()
        if current_text != expected:
            similarity = self._text_similarity(current_text, expected)
            if similarity < 0.5:
                logger.warning(
                    f"第{slide_idx}页 shape_index {mod.shape_index} 文本不匹配 "
                    f"(相似度 {similarity:.0%}), 跳过. "
                    f"期望: {expected[:50]}... 实际: {current_text[:50]}..."
                )
                return False
            logger.info(
                f"第{slide_idx}页 shape_index {mod.shape_index} 文本部分匹配 "
                f"(相似度 {similarity:.0%}), 继续写入"
            )

        self._replace_text_preserve_format(shape, mod.new_text)
        logger.debug(
            f"第{slide_idx}页 shape_{mod.shape_index}: "
            f"'{expected[:30]}...' → '{mod.new_text[:30]}...'"
        )
        return True

    def _apply_table_modification(
        self, shapes: list, mod: TableCellModification, slide_idx: int
    ) -> bool:
        """应用单个表格单元格修改"""
        if mod.shape_index >= len(shapes):
            logger.warning(
                f"第{slide_idx}页 shape_index {mod.shape_index} 超出范围, 跳过"
            )
            return False

        shape = shapes[mod.shape_index]

        if not shape.has_table:
            logger.warning(
                f"第{slide_idx}页 shape_index {mod.shape_index} 不是表格, 跳过"
            )
            return False

        table = shape.table
        if mod.row >= len(table.rows) or mod.col >= len(table.columns):
            logger.warning(
                f"第{slide_idx}页 表格 shape_{mod.shape_index} "
                f"行列索引 ({mod.row},{mod.col}) 超出范围 "
                f"({len(table.rows)}行×{len(table.columns)}列), 跳过"
            )
            return False

        cell = table.cell(mod.row, mod.col)
        self._replace_cell_text(cell, mod.new_text)
        logger.debug(
            f"第{slide_idx}页 表格 shape_{mod.shape_index} "
            f"({mod.row},{mod.col}): '{mod.original_text[:20]}' → '{mod.new_text[:20]}'"
        )
        return True

    def _replace_text_preserve_format(self, shape, new_text: str):
        """
        Run 级别文本替换 — 保留格式的核心算法。

        策略:
          1. 将新文本按换行符分割为段落
          2. 对于每个新段落:
             - 如果对应位置有旧段落: 替换第一个 Run 文本，清空后续 Run
             - 如果没有旧段落: 追加新段落，继承最后一段格式
          3. 多余的旧段落: 清空文本（保留段落结构避免 XML 异常）
        """
        tf = shape.text_frame
        new_paras = new_text.split("\n")
        old_paras = list(tf.paragraphs)

        for i, new_para_text in enumerate(new_paras):
            if i < len(old_paras):
                self._replace_paragraph_text(old_paras[i], new_para_text)
            else:
                new_para = tf.add_paragraph()
                new_para.text = new_para_text
                if old_paras:
                    self._copy_paragraph_format(old_paras[-1], new_para)

        for i in range(len(new_paras), len(old_paras)):
            self._clear_paragraph(old_paras[i])

    def _replace_paragraph_text(self, para, new_text: str):
        """替换段落文本，保留第一个 Run 的格式"""
        runs = list(para.runs)
        if runs:
            runs[0].text = new_text
            for run in runs[1:]:
                run.text = ""
        else:
            para.text = new_text

    def _clear_paragraph(self, para):
        """清空段落文本（保留段落节点）"""
        for run in para.runs:
            run.text = ""

    def _replace_cell_text(self, cell, new_text: str):
        """替换表格单元格文本"""
        if cell.text_frame.paragraphs:
            para = cell.text_frame.paragraphs[0]
            runs = list(para.runs)
            if runs:
                runs[0].text = new_text
                for run in runs[1:]:
                    run.text = ""
            else:
                para.text = new_text
            for p in list(cell.text_frame.paragraphs)[1:]:
                for run in p.runs:
                    run.text = ""

    def _copy_paragraph_format(self, source_para, target_para):
        """复制段落格式"""
        try:
            if source_para.alignment is not None:
                target_para.alignment = source_para.alignment
        except Exception:
            pass

        try:
            if source_para.level is not None:
                target_para.level = source_para.level
        except Exception:
            pass

        try:
            src_runs = list(source_para.runs)
            tgt_runs = list(target_para.runs)
            if src_runs and tgt_runs:
                sf = src_runs[0].font
                tf = tgt_runs[0].font
                if sf.name:
                    tf.name = sf.name
                if sf.size:
                    tf.size = sf.size
                if sf.bold is not None:
                    tf.bold = sf.bold
                if sf.italic is not None:
                    tf.italic = sf.italic
                try:
                    if sf.color and sf.color.rgb:
                        tf.color.rgb = sf.color.rgb
                except Exception:
                    pass
        except Exception:
            pass

    def compose(
        self,
        source_files: dict[str, Path],
        selections: list[SlideSelector],
        output_dir: Path,
    ) -> Path:
        """
        从多个 PPTX 中选择页面，组合为新 PPTX。

        Args:
            source_files: {"ppt_a": Path, "ppt_b": Path, ...}
            selections: 按顺序选择的页面列表
            output_dir: 输出目录

        Returns:
            新 PPTX 文件路径
        """
        from copy import deepcopy
        from lxml import etree

        if not selections:
            raise ValueError("至少需要选择一页")

        first_source = selections[0].source
        first_path = source_files.get(first_source)
        if not first_path:
            raise ValueError(f"找不到源文件: {first_source}")

        base_prs = Presentation(str(first_path))

        presentations = {}
        for key, path in source_files.items():
            presentations[key] = Presentation(str(path))

        existing_slides = list(base_prs.slides)
        for slide in existing_slides:
            rId = base_prs.slides._sldIdLst[-1].get(qn("r:id"))
            base_prs.part.drop_rel(rId)
            base_prs.slides._sldIdLst.remove(base_prs.slides._sldIdLst[-1])

        for sel in selections:
            src_prs = presentations.get(sel.source)
            if not src_prs:
                logger.warning(f"源 {sel.source} 不存在, 跳过")
                continue
            if sel.slide_index >= len(src_prs.slides):
                logger.warning(
                    f"源 {sel.source} 页码 {sel.slide_index} 超出范围, 跳过"
                )
                continue

            src_slide = src_prs.slides[sel.slide_index]
            self._copy_slide(base_prs, src_slide, src_prs)

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"composed_{uuid4().hex[:8]}.pptx"
        base_prs.save(str(output_path))

        logger.info(f"组合完成: {output_path.name}, {len(selections)} 页")
        return output_path

    def _copy_slide(self, dest_prs, src_slide, src_prs):
        """将一页幻灯片从源复制到目标演示文稿"""
        from copy import deepcopy
        from pptx.opc.constants import RELATIONSHIP_TYPE as RT

        slide_layout = dest_prs.slide_layouts[6]  # blank layout as fallback
        new_slide = dest_prs.slides.add_slide(slide_layout)

        for shape in new_slide.shapes:
            sp = shape._element
            sp.getparent().remove(sp)

        for shape in src_slide.shapes:
            el = deepcopy(shape._element)
            new_slide.shapes._spTree.append(el)

        for rel in src_slide.part.rels.values():
            if "image" in rel.reltype:
                try:
                    new_slide.part.rels.get_or_add(
                        rel.rId, rel.reltype, rel.target_part
                    )
                except Exception:
                    pass

    def _text_similarity(self, a: str, b: str) -> float:
        """简单的文本相似度（字符级 Jaccard）"""
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        set_a = set(a)
        set_b = set(b)
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union) if union else 0.0
