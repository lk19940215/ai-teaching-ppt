"""
完整管线追踪：记录每个节点的真实数据

流程：PPTX文件 → 解析 → 提取AI内容 → 格式化AI输入 → 模拟AI输出 → 解析AI响应 → 写回 → 验证

每个阶段打印完整的数据结构，用于：
1. 理解数据在管线中的变化
2. 验证 prompt_template.md 的设计是否匹配真实数据
3. 确认往返质量
"""

import sys
import os
import json

os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pathlib import Path
from app.core.pptx_reader import PPTXReader
from app.core.content_extractor import ContentExtractor
from app.core.pptx_writer import PPTXWriter
from app.core.models import (
    TextModification, TableCellModification, SlideModification, ProcessingResult
)
from app.ai.prompts import build_prompt


def trace(test_pptx: str):
    reader = PPTXReader()
    extractor = ContentExtractor()
    writer = PPTXWriter()

    print("=" * 70)
    print("完整管线追踪")
    print("=" * 70)

    # ================================================================
    # Stage 1: PPTX → ParsedPresentation
    # ================================================================
    print("\n" + "▓" * 70)
    print("▓ Stage 1: PPTX 解析 → ParsedPresentation")
    print("▓" * 70)

    parsed = reader.parse(Path(test_pptx))
    print(f"\n文件: {parsed.filename}")
    print(f"页数: {parsed.slide_count}")
    print(f"尺寸: {parsed.slide_width}x{parsed.slide_height} EMU")

    for slide in parsed.slides:
        print(f"\n--- slide[{slide.slide_index}] (版式: {slide.layout_name}) ---")
        print(f"  has_animations: {slide.has_animations}")
        print(f"  has_media: {slide.has_media}")
        print(f"  has_notes: {slide.has_notes}")
        print(f"  elements: {len(slide.elements)} 个")

        for elem in slide.elements:
            print(f"\n  elements[{elem.shape_index}]:")
            print(f"    type: {elem.element_type.value}")
            print(f"    name: {elem.name}")
            print(f"    position: left={elem.position.left}, top={elem.position.top}, "
                  f"w={elem.position.width}, h={elem.position.height}")
            print(f"    is_title: {elem.is_title}")
            print(f"    is_placeholder: {elem.is_placeholder}")
            print(f"    placeholder_type: {elem.placeholder_type}")

            if elem.plain_text:
                text_preview = elem.plain_text[:80].replace('\n', '\\n')
                print(f"    plain_text: \"{text_preview}\"")
                print(f"    paragraphs: {len(elem.paragraphs)} 个")
                for pi, para in enumerate(elem.paragraphs[:3]):
                    print(f"      para[{pi}]: alignment={para.alignment}, level={para.level}")
                    for ri, run in enumerate(para.runs[:3]):
                        run_text = run.text[:40].replace('\n', '\\n')
                        fmt = []
                        if run.bold: fmt.append("bold")
                        if run.italic: fmt.append("italic")
                        if run.font_size: fmt.append(f"{run.font_size}pt")
                        if run.font_color: fmt.append(run.font_color)
                        if run.font_name: fmt.append(run.font_name)
                        print(f"        run[{ri}]: \"{run_text}\" [{', '.join(fmt)}]")

            if elem.table_data:
                print(f"    table: {elem.table_rows}行 x {elem.table_cols}列")
                for ri, row in enumerate(elem.table_data[:3]):
                    cells = [c.text[:15] for c in row[:5]]
                    print(f"      row[{ri}]: {cells}")

    # ================================================================
    # Stage 2: ParsedPresentation → SlideContent (AI 友好层)
    # ================================================================
    print("\n" + "▓" * 70)
    print("▓ Stage 2: 内容提取 → SlideContent (AI 友好的第二层)")
    print("▓" * 70)

    contents = extractor.extract_all(parsed)
    for content in contents:
        print(f"\n--- SlideContent[{content.slide_index}] ---")
        print(f"  title: {content.title}")
        print(f"  has_images: {content.has_images}")
        print(f"  has_media: {content.has_media}")

        print(f"  text_blocks: {len(content.text_blocks)} 个")
        for tb in content.text_blocks:
            print(f"    TextBlock(shape_index={tb.shape_index}, role=\"{tb.role}\", "
                  f"text=\"{tb.text[:50]}\")")

        print(f"  table_blocks: {len(content.table_blocks)} 个")
        for tb in content.table_blocks:
            print(f"    TableBlock(shape_index={tb.shape_index}, "
                  f"headers={tb.headers[:5]}, rows={len(tb.rows)}行)")

    # ================================================================
    # Stage 3: SlideContent → format_for_ai → 传给 AI 的文本
    # ================================================================
    print("\n" + "▓" * 70)
    print("▓ Stage 3: format_for_ai → 传给 AI 的纯文本输入")
    print("▓" * 70)

    for content in contents:
        ai_text = extractor.format_for_ai(content)
        print(f"\n--- 第 {content.slide_index + 1} 页传给 AI 的文本 ---")
        print("┌" + "─" * 60 + "┐")
        for line in ai_text.split("\n"):
            print(f"│ {line:<58} │")
        print("└" + "─" * 60 + "┘")

    # ================================================================
    # Stage 4: build_prompt → 完整的 messages (system + user)
    # ================================================================
    print("\n" + "▓" * 70)
    print("▓ Stage 4: build_prompt → 发给 LLM 的完整 messages")
    print("▓" * 70)

    if contents:
        sample_content = contents[0]
        ai_text = extractor.format_for_ai(sample_content)
        messages = build_prompt(ai_text, "polish")

        print(f"\n消息数: {len(messages)}")
        for i, msg in enumerate(messages):
            role = msg["role"]
            content_text = msg["content"]
            print(f"\n--- messages[{i}] role=\"{role}\" ({len(content_text)} 字) ---")
            if role == "system":
                print("  [系统提示词，即 prompt_template.md 注入后的内容]")
                lines = content_text.split("\n")
                for line in lines[:5]:
                    print(f"  {line}")
                print(f"  ... (共 {len(lines)} 行)")
                for line in lines[-5:]:
                    print(f"  {line}")
            else:
                print("┌" + "─" * 60 + "┐")
                for line in content_text.split("\n"):
                    print(f"│ {line:<58} │")
                print("└" + "─" * 60 + "┘")

    # ================================================================
    # Stage 5: 模拟 AI 返回的 JSON（这是 AI 应该返回的格式）
    # ================================================================
    print("\n" + "▓" * 70)
    print("▓ Stage 5: 模拟 AI 返回的 JSON 数据")
    print("▓" * 70)

    mock_ai_responses = []
    for content in contents:
        if content.text_blocks:
            tb = content.text_blocks[0]
            response = {
                "text_blocks": [{
                    "shape_index": tb.shape_index,
                    "new_text": tb.text + "（AI润色后）"
                }],
                "table_cells": [],
                "summary": f"润色了第{content.slide_index+1}页的文本"
            }
            if content.table_blocks:
                ttb = content.table_blocks[0]
                if ttb.rows:
                    response["table_cells"].append({
                        "shape_index": ttb.shape_index,
                        "row": 1,
                        "col": 0,
                        "new_text": ttb.rows[0][0] + "（AI修改）"
                    })
            mock_ai_responses.append((content, response))
            print(f"\n--- 第 {content.slide_index+1} 页 AI 返回 ---")
            print(json.dumps(response, ensure_ascii=False, indent=2))

    # ================================================================
    # Stage 6: _parse_response → SlideModification (修改指令)
    # ================================================================
    print("\n" + "▓" * 70)
    print("▓ Stage 6: 解析 AI 响应 → SlideModification 修改指令")
    print("▓" * 70)

    from app.ai.processor import AIProcessor
    from app.ai.llm_client import LLMClient

    dummy_client = LLMClient.__new__(LLMClient)
    processor = AIProcessor.__new__(AIProcessor)
    processor.llm = dummy_client
    processor.extractor = extractor

    all_modifications = []
    for content, response in mock_ai_responses:
        slide_mod = processor._parse_response(response, content)
        all_modifications.append(slide_mod)

        print(f"\n--- SlideModification[slide_index={slide_mod.slide_index}] ---")
        print(f"  text_modifications: {len(slide_mod.text_modifications)} 个")
        for tm in slide_mod.text_modifications:
            print(f"    TextModification(shape_index={tm.shape_index})")
            print(f"      original: \"{tm.original_text[:40]}\"")
            print(f"      new:      \"{tm.new_text[:40]}\"")

        print(f"  table_modifications: {len(slide_mod.table_modifications)} 个")
        for tcm in slide_mod.table_modifications:
            print(f"    TableCellModification(shape_index={tcm.shape_index}, "
                  f"row={tcm.row}, col={tcm.col})")
            print(f"      original: \"{tcm.original_text[:40]}\"")
            print(f"      new:      \"{tcm.new_text[:40]}\"")

        print(f"  ai_summary: {slide_mod.ai_summary}")

    # ================================================================
    # Stage 7: 写回 → 新 PPTX
    # ================================================================
    print("\n" + "▓" * 70)
    print("▓ Stage 7: PPTXWriter.apply → 写回新 PPTX")
    print("▓" * 70)

    output_dir = Path(test_pptx).parent
    output_path = writer.apply(Path(test_pptx), all_modifications, output_dir)
    print(f"\n  输出: {output_path}")

    # ================================================================
    # Stage 8: 重新解析验证
    # ================================================================
    print("\n" + "▓" * 70)
    print("▓ Stage 8: 重新解析验证")
    print("▓" * 70)

    parsed2 = reader.parse(output_path)
    checks = []

    checks.append(("页数", parsed.slide_count == parsed2.slide_count,
                   f"{parsed.slide_count} → {parsed2.slide_count}"))

    for s1, s2 in zip(parsed.slides, parsed2.slides):
        checks.append((f"第{s1.slide_index+1}页动画", s1.has_animations == s2.has_animations,
                       f"{s1.has_animations} → {s2.has_animations}"))

        for e1, e2 in zip(s1.elements, s2.elements):
            if e1.paragraphs and e2.paragraphs:
                for p1, p2 in zip(e1.paragraphs, e2.paragraphs):
                    for r1, r2 in zip(p1.runs, p2.runs):
                        fmt_ok = (r1.bold == r2.bold and r1.italic == r2.italic and
                                  r1.font_size == r2.font_size and r1.font_name == r2.font_name)
                        if not fmt_ok:
                            checks.append((f"第{s1.slide_index+1}页格式", False,
                                          f"bold:{r1.bold}→{r2.bold}"))

    for elem in parsed2.slides[0].elements if parsed2.slides else []:
        if elem.plain_text and "AI润色后" in elem.plain_text:
            checks.append(("文本修改生效", True, "包含 'AI润色后'"))
            break

    print("\n" + "=" * 60)
    print("验证报告")
    print("=" * 60)
    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    # 清理
    try:
        os.unlink(output_path)
    except:
        pass

    print("\n=== 追踪完成 ===")


if __name__ == "__main__":
    import glob
    candidates = [
        "E:\\Code\\ai-teaching-ppt\\backend\\test_downloaded.pptx",
    ]
    # 查找真实 PPTX
    for g in glob.glob("E:\\Code\\ai-teaching-ppt\\uploads\\generated\\*.pptx"):
        candidates.insert(0, g)

    test_file = None
    for c in candidates:
        if os.path.exists(c):
            test_file = c
            break

    if not test_file:
        print("未找到测试 PPTX 文件！")
        sys.exit(1)

    print(f"使用测试文件: {test_file}")
    trace(test_file)
