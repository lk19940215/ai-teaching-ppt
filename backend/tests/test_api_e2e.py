"""
端到端 API 测试

测试: 上传真实 PPT → 查看解析结果 → (可选)AI处理
"""
import sys
import os
import json
import requests
from pathlib import Path

if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

_PORT = os.environ.get("BACKEND_PORT", "9501")
BASE_URL = f"http://localhost:{_PORT}/api/v1/ppt"


def test_upload():
    """测试上传"""
    pptx_path = Path(r"E:\Code\ai-teaching-ppt\uploads\generated\test_大龙猫.pptx")
    if not pptx_path.exists():
        print(f"文件不存在: {pptx_path}")
        return None

    print(f"=== 上传测试 ===")
    print(f"文件: {pptx_path.name} ({pptx_path.stat().st_size} bytes)")

    with open(pptx_path, "rb") as f:
        files = {"file_a": (pptx_path.name, f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
        resp = requests.post(f"{BASE_URL}/upload", files=files)

    print(f"状态码: {resp.status_code}")

    if resp.status_code != 200:
        print(f"错误: {resp.text[:500]}")
        return None

    data = resp.json()
    session_id = data["session_id"]
    parsed = data["parsed"]

    print(f"会话 ID: {session_id}")
    print(f"预览图数: {len(data.get('preview_images', []))}")

    for key, ppt_data in parsed.items():
        print(f"\n--- {key} ---")
        print(f"  文件名: {ppt_data['filename']}")
        print(f"  页数: {ppt_data['slide_count']}")
        for slide in ppt_data["slides"]:
            idx = slide["slide_index"]
            elems = slide["elements"]
            text_elems = [e for e in elems if e.get("plain_text")]
            table_elems = [e for e in elems if e.get("table_data")]
            img_elems = [e for e in elems if e.get("image_base64")]
            print(f"  第{idx+1}页: {len(text_elems)}文本 {len(table_elems)}表格 {len(img_elems)}图片")
            for e in text_elems:
                txt = e["plain_text"][:60].replace("\n", "\\n")
                title_tag = " [标题]" if e.get("is_title") else ""
                print(f"    [{e['shape_index']}] {txt}{title_tag}")

    return session_id


def test_versions(session_id):
    """测试版本列表"""
    print(f"\n=== 版本历史 ===")
    resp = requests.get(f"{BASE_URL}/versions/{session_id}")
    print(f"状态码: {resp.status_code}")

    if resp.status_code == 200:
        data = resp.json()
        print(f"版本数: {len(data['versions'])}")
        for v in data["versions"]:
            print(f"  v{v['version_number']} ({v['version_id']}): {v['action']} - {v.get('description', '')[:50]}")
    return resp.status_code == 200


def test_download(session_id, version_id=None):
    """测试下载"""
    print(f"\n=== 下载测试 ===")
    if version_id:
        url = f"{BASE_URL}/download/{session_id}/{version_id}"
    else:
        url = f"{BASE_URL}/download/{session_id}"

    resp = requests.get(url)
    print(f"状态码: {resp.status_code}")

    if resp.status_code == 200:
        content_type = resp.headers.get("content-type", "")
        size = len(resp.content)
        print(f"Content-Type: {content_type}")
        print(f"文件大小: {size} bytes")

        out_path = Path(f"test_download_{session_id[:6]}.pptx")
        out_path.write_bytes(resp.content)
        print(f"已保存到: {out_path}")
        return True

    print(f"错误: {resp.text[:200]}")
    return False


def main():
    print("=" * 60)
    print("API 端到端测试")
    print("=" * 60)

    session_id = test_upload()
    if not session_id:
        return 1

    test_versions(session_id)
    test_download(session_id)

    print("\n" + "=" * 60)
    print("API 基础测试通过！")
    print(f"Swagger UI: http://localhost:{_PORT}/docs")
    print(f"会话 ID: {session_id}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
