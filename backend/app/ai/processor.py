"""
AI 内容处理器

编排 ContentExtractor → LLM → ProcessingResult 的完整流程。
每次处理立即生成新版本的 PPTX 文件。
"""

import json
import logging
from typing import Optional, TYPE_CHECKING

from ..core.models import (
    SlideContent, SlideModification,
    TextModification, TableCellModification, ProcessingResult,
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

    def process_slide(
        self,
        content: SlideContent,
        action: str,
        custom_prompt: Optional[str] = None,
    ) -> ProcessingResult:
        """
        处理单页幻灯片。

        Args:
            content: 从 ContentExtractor 提取的页面内容
            action: polish / expand / rewrite / extract
            custom_prompt: 用户自定义提示

        Returns:
            ProcessingResult 包含修改指令
        """
        ai_text = self.extractor.format_for_ai(content)
        messages = build_prompt(ai_text, action, custom_prompt)

        if self._slog:
            self._slog.info(f"LLM 调用 - 第{content.slide_index + 1}页 [{action}]")
            self._slog.dump("SYSTEM PROMPT", messages[0]["content"])
            self._slog.dump("USER INPUT", messages[1]["content"])

        try:
            data = self.llm.chat_json(messages)
        except Exception as e:
            logger.error(f"AI 处理失败: {e}")
            if self._slog:
                self._slog.error(f"LLM 调用失败 - 第{content.slide_index + 1}页", exception=str(e))
            return ProcessingResult(
                success=False,
                action=action,
                error=str(e),
            )

        if self._slog:
            self._slog.dump("LLM OUTPUT", json.dumps(data, ensure_ascii=False, indent=2))

        slide_mod = self._parse_response(data, content)

        total = len(slide_mod.text_modifications) + len(slide_mod.table_modifications)

        return ProcessingResult(
            success=True,
            modifications=[slide_mod],
            action=action,
            total_changes=total,
        )

    def process_slides(
        self,
        contents: list[SlideContent],
        action: str,
        custom_prompt: Optional[str] = None,
    ) -> ProcessingResult:
        """处理多页幻灯片（逐页调用 LLM）"""
        all_mods = []
        total = 0
        errors = []

        for content in contents:
            result = self.process_slide(content, action, custom_prompt)
            if result.success:
                all_mods.extend(result.modifications)
                total += result.total_changes
            else:
                errors.append(f"第{content.slide_index+1}页: {result.error}")

        if errors and not all_mods:
            return ProcessingResult(
                success=False,
                action=action,
                error="; ".join(errors),
            )

        return ProcessingResult(
            success=True,
            modifications=all_mods,
            action=action,
            total_changes=total,
            error="; ".join(errors) if errors else None,
        )

    def _parse_response(
        self, data: dict, content: SlideContent
    ) -> SlideModification:
        """解析 LLM 返回的 JSON → SlideModification"""
        text_mods = []
        table_mods = []

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

            text_mods.append(TextModification(
                shape_index=shape_idx,
                original_text=original.text,
                new_text=new_text,
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

        return SlideModification(
            slide_index=content.slide_index,
            text_modifications=text_mods,
            table_modifications=table_mods,
            ai_summary=data.get("summary"),
        )
