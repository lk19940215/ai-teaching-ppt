"""测试真实 PPTX 文件的解析效果"""
import sys
import os
from pathlib import Path

if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.pptx_reader import PPTXReader
from app.core.content_extractor import ContentExtractor


def main():
    pptx_path = Path(r"E:\Code\ai-teaching-ppt\uploads\generated\test_大龙猫.pptx")
    if not pptx_path.exists():
        print(f"文件不存在: {pptx_path}")
        return 1

    reader = PPTXReader()
    parsed = reader.parse(pptx_path)

    print(f"文件: {parsed.filename}")
    print(f"页数: {parsed.slide_count}")
    print(f"尺寸: {parsed.slide_width}x{parsed.slide_height} EMU")
    print(f"标题: {parsed.title}")
    print()

    extractor = ContentExtractor()

    for slide in parsed.slides:
        print(f"=== 第 {slide.slide_index + 1} 页 (版式: {slide.layout_name}) ===")
        print(f"  动画: {slide.has_animations}, 媒体: {slide.has_media}, 备注: {slide.has_notes}")

        for elem in slide.elements:
            type_str = elem.element_type.value
            prefix = "[标题] " if elem.is_title else ""

            if elem.plain_text:
                text = elem.plain_text[:80].replace("\n", "\\n")
                print(f"  [{elem.shape_index}] {type_str} {prefix}\"{text}\"")
                if elem.paragraphs:
                    for pi, p in enumerate(elem.paragraphs[:4]):
                        for ri, r in enumerate(p.runs[:2]):
                            fmts = []
                            if r.bold:
                                fmts.append("B")
                            if r.italic:
                                fmts.append("I")
                            if r.font_size:
                                fmts.append(f"{r.font_size}pt")
                            if r.font_color:
                                fmts.append(r.font_color)
                            if r.font_name:
                                fmts.append(r.font_name)
                            fmt = ",".join(fmts) if fmts else "default"
                            print(f"    P{pi}R{ri} [{fmt}]: \"{r.text[:50]}\"")
                        if len(p.runs) > 2:
                            print(f"    P{pi} ... 还有 {len(p.runs)-2} 个 Run")
                    if len(elem.paragraphs) > 4:
                        print(f"    ... 还有 {len(elem.paragraphs)-4} 个段落")

            elif elem.table_data:
                print(f"  [{elem.shape_index}] {type_str} {elem.table_rows}行x{elem.table_cols}列")
                for ri, row in enumerate(elem.table_data[:3]):
                    cells = [c.text[:20] for c in row]
                    print(f"    行{ri}: {cells}")
                if len(elem.table_data) > 3:
                    print(f"    ... 还有 {len(elem.table_data)-3} 行")

            elif elem.image_base64:
                b64_len = len(elem.image_base64)
                print(f"  [{elem.shape_index}] {type_str} [图片 {elem.image_format}, base64 {b64_len} chars]")

            else:
                print(f"  [{elem.shape_index}] {type_str} (name={elem.name})")

        content = extractor.extract_slide(slide)
        ai_text = extractor.format_for_ai(content)
        lines = ai_text.split("\n")
        print(f"  --- AI视图 ({len(lines)}行) ---")
        for line in lines[:8]:
            print(f"  {line}")
        if len(lines) > 8:
            print(f"  ... 省略 {len(lines)-8} 行")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
