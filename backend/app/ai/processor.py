"""
AI 内容处理器

编排 ContentExtractor → LLM → ProcessingResult 的完整流程。
支持单页和多页批量处理 — 多页时一次性发送给 LLM。
"""

import json
import logging
from typing import Optional, TYPE_CHECKING

from ..core.models import (
    SlideContent, SlideModification, NewSlideContent,
    TextModification, TableCellModification, ProcessingResult,
    StyleHints, AnimationHint,
)
from ..core.content_extractor import ContentExtractor
from .llm_client import LLMClient
from .prompts import build_prompt

if TYPE_CHECKING:
    from ..core.session_logger import SessionLogger

logger = logging.getLogger(__name__)


class AIProcessor:
    """AI 内容处理器"""

    def __init__(self, llm_client: LLMClient, session_logger: Optional["SessionLogger"] = None):
        self.llm = llm_client
        self.extractor = ContentExtractor()
        self._slog = session_logger

    def process_slides(
        self,
        contents: list[SlideContent],
        action: str,
        domain: Optional[str] = None,
        custom_prompt: Optional[str] = None,
    ) -> ProcessingResult:
        """
        处理一页或多页幻灯片 — 一次性发送给 LLM。

        单页时使用 format_for_ai，多页时使用 format_multi_for_ai，
        让 AI 完整理解所有页面后统一返回 slides[] 数组。
        """
        ai_text = self.extractor.format_multi_for_ai(contents)
        messages = build_prompt(ai_text, action, domain=domain, custom_prompt=custom_prompt)

        slide_desc = ", ".join(f"第{c.slide_index + 1}页" for c in contents)
        if self._slog:
            self._slog.info(
                f"LLM 调用 - {slide_desc} [{action}] domain={domain or '_default'}"
            )
            self._slog.dump("SYSTEM PROMPT", messages[0]["content"])
            self._slog.dump("USER INPUT", messages[1]["content"])

        try:
            data = self.llm.chat_json(messages)
        except Exception as e:
            logger.error(f"AI 处理失败: {e}")
            if self._slog:
                self._slog.error(f"LLM 调用失败 - {slide_desc}", exception=str(e))
            return ProcessingResult(
                success=False,
                action=action,
                error=str(e),
            )

        if self._slog:
            self._slog.dump("LLM OUTPUT", json.dumps(data, ensure_ascii=False, indent=2))

        content_map = {c.slide_index: c for c in contents}
        all_mods = self._parse_multi_response(data, content_map)

        total = sum(
            len(m.text_modifications) + len(m.table_modifications)
            for m in all_mods
        )

        return ProcessingResult(
            success=True,
            modifications=all_mods,
            action=action,
            total_changes=total,
        )

    def _parse_multi_response(
        self, data: dict, content_map: dict[int, SlideContent]
    ) -> list[SlideModification]:
        """解析 LLM 返回的 JSON → SlideModification 列表

        支持两种格式：
        1. slides[] 数组（新格式，多页）
        2. 顶层 text_blocks/table_cells（旧格式兼容，单页）
        """
        slides_data = data.get("slides")
        top_summary = data.get("summary", "")

        if slides_data and isinstance(slides_data, list):
            mods = []
            for slide_data in slides_data:
                if not isinstance(slide_data, dict):
                    continue

                is_new = slide_data.get("is_new", False)
                slide_idx = slide_data.get("slide_index", -1)

                if is_new:
                    mod = self._parse_new_slide(slide_data)
                    if not mod.ai_summary:
                        mod.ai_summary = top_summary
                    mods.append(mod)
                else:
                    content = content_map.get(slide_idx)
                    if content is None:
                        logger.warning(
                            f"slides[] 中 slide_index={slide_idx} 不在输入中, 跳过"
                        )
                        continue
                    mod = self._parse_single_slide(slide_data, content)
                    if not mod.ai_summary:
                        mod.ai_summary = top_summary
                    mods.append(mod)
            return mods

        # 旧格式兼容：顶层 text_blocks/table_cells
        if content_map:
            first_content = next(iter(content_map.values()))
            mod = self._parse_single_slide(data, first_content)
            return [mod]

        return []

    def _parse_single_slide(
        self, data: dict, content: SlideContent
    ) -> SlideModification:
        """解析单页修改指令（已有页面）"""
        text_mods = []
        table_mods = []
        anim_hints = []

        text_block_map = {tb.shape_index: tb for tb in content.text_blocks}
        table_block_map = {tb.shape_index: tb for tb in content.table_blocks}

        for block in data.get("text_blocks", []):
            shape_idx = block.get("shape_index")
            new_text = block.get("new_text", "")
            if shape_idx is None or not new_text:
                continue

            original = text_block_map.get(shape_idx)
            if original is None:
                logger.warning(f"shape_index {shape_idx} 不在提取的文本块中, 跳过")
                continue

            if original.text.strip() == new_text.strip():
                continue

            style = None
            raw_hints = block.get("style_hints")
            if raw_hints and isinstance(raw_hints, dict):
                style = StyleHints(**{
                    k: v for k, v in raw_hints.items()
                    if k in StyleHints.model_fields
                })

            text_mods.append(TextModification(
                shape_index=shape_idx,
                original_text=original.text,
                new_text=new_text,
                style_hints=style,
            ))

        for cell in data.get("table_cells", []):
            shape_idx = cell.get("shape_index")
            row = cell.get("row")
            col = cell.get("col")
            new_text = cell.get("new_text", "")
            if shape_idx is None or row is None or col is None:
                continue

            table = table_block_map.get(shape_idx)
            if table is None:
                continue

            original_text = ""
            if row == 0 and col < len(table.headers):
                original_text = table.headers[col]
            elif row > 0 and (row - 1) < len(table.rows):
                row_data = table.rows[row - 1]
                if col < len(row_data):
                    original_text = row_data[col]

            if original_text.strip() == new_text.strip():
                continue

            table_mods.append(TableCellModification(
                shape_index=shape_idx,
                row=row,
                col=col,
                original_text=original_text,
                new_text=new_text,
            ))

        for hint_raw in data.get("animation_hints", []):
            if not isinstance(hint_raw, dict):
                continue
            shape_idx = hint_raw.get("shape_index")
            if shape_idx is None:
                continue
            try:
                anim_hints.append(AnimationHint(
                    shape_index=shape_idx,
                    effect=hint_raw.get("effect", "fade"),
                    trigger=hint_raw.get("trigger", "on_click"),
                    duration_ms=hint_raw.get("duration_ms"),
                ))
            except Exception as e:
                logger.warning(f"解析 animation_hint 失败: {e}")

        return SlideModification(
            slide_index=content.slide_index,
            text_modifications=text_mods,
            table_modifications=table_mods,
            animation_hints=anim_hints,
            ai_summary=data.get("summary"),
        )

    def _parse_new_slide(self, data: dict) -> SlideModification:
        """解析 AI 要求创建的新页面"""
        title = data.get("title", "")
        body_texts = data.get("body_texts", [])
        layout_hint = data.get("layout_hint", "blank")

        anim_hints = []
        for hint_raw in data.get("animation_hints", []):
            if not isinstance(hint_raw, dict):
                continue
            try:
                anim_hints.append(AnimationHint(
                    shape_index=hint_raw.get("shape_index", 0),
                    effect=hint_raw.get("effect", "fade"),
                    trigger=hint_raw.get("trigger", "on_click"),
                    duration_ms=hint_raw.get("duration_ms"),
                ))
            except Exception:
                pass

        return SlideModification(
            slide_index=-1,
            is_new_slide=True,
            new_slide_content=NewSlideContent(
                title=title,
                body_texts=body_texts,
                layout_hint=layout_hint,
            ),
            animation_hints=anim_hints,
            ai_summary=data.get("summary"),
        )
