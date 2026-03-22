"""
内容提取器

从 ParsedPresentation (第一层) 提取 AI 友好的纯文本内容 (第二层)。
通过 shape_index 维持与原始 Shape 的映射关系。

技术文档: docs/technical-spec.md §5.2
"""

from .models import (
    ElementType, SlideElement, ParsedSlide, ParsedPresentation,
    TextBlock, TableBlock, SlideContent,
)


class ContentExtractor:
    """内容提取器：ParsedPresentation → SlideContent 列表"""

    def extract_slide(self, slide: ParsedSlide) -> SlideContent:
        """从单页提取 AI 可处理的文本内容"""
        text_blocks: list[TextBlock] = []
        table_blocks: list[TableBlock] = []
        title = None

        for elem in slide.elements:
            if elem.element_type == ElementType.TEXT_BOX and elem.plain_text:
                role = "title" if elem.is_title else "body"
                if elem.placeholder_type == "subtitle":
                    role = "subtitle"

                text_blocks.append(TextBlock(
                    shape_index=elem.shape_index,
                    role=role,
                    text=elem.plain_text,
                ))

                if elem.is_title and title is None:
                    title = elem.plain_text

            elif elem.element_type == ElementType.TABLE and elem.table_data:
                headers = []
                rows = []
                for row_idx, row in enumerate(elem.table_data):
                    row_texts = [cell.text for cell in row]
                    if row_idx == 0:
                        headers = row_texts
                    else:
                        rows.append(row_texts)

                table_blocks.append(TableBlock(
                    shape_index=elem.shape_index,
                    headers=headers,
                    rows=rows,
                ))

        has_images = any(
            e.element_type == ElementType.IMAGE for e in slide.elements
        )

        return SlideContent(
            slide_index=slide.slide_index,
            title=title,
            text_blocks=text_blocks,
            table_blocks=table_blocks,
            has_images=has_images,
            has_media=slide.has_media,
            has_animations=slide.has_animations,
            layout_name=slide.layout_name,
            element_count=len(slide.elements),
        )

    def extract_all(self, presentation: ParsedPresentation) -> list[SlideContent]:
        """提取所有页面的内容"""
        return [self.extract_slide(slide) for slide in presentation.slides]

    def format_for_ai(self, content: SlideContent) -> str:
        """将 SlideContent 格式化为 AI 可读的文本描述"""
        parts = []

        # 页面上下文信息
        ctx_items = []
        if content.layout_name:
            ctx_items.append(f"版式={content.layout_name}")
        ctx_items.append(f"共{content.element_count}个元素")
        if content.has_animations:
            ctx_items.append("含入场动画")
        if content.has_images:
            ctx_items.append("含图片")
        if content.has_media:
            ctx_items.append("含音视频")
        parts.append(f"【页面信息】{', '.join(ctx_items)}")

        if content.title:
            parts.append(f"【标题】{content.title}")

        for block in content.text_blocks:
            if block.role == "title":
                continue
            label = {"body": "正文", "subtitle": "副标题", "note": "备注"}.get(block.role, "文本")
            parts.append(f"【{label}·shape_{block.shape_index}】{block.text}")

        for table in content.table_blocks:
            header_str = " | ".join(table.headers) if table.headers else ""
            parts.append(f"【表格·shape_{table.shape_index}】")
            if header_str:
                parts.append(f"  表头: {header_str}")
            for row_idx, row in enumerate(table.rows):
                parts.append(f"  第{row_idx + 1}行: {' | '.join(row)}")

        return "\n".join(parts)
