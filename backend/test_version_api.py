# -*- coding: utf-8 -*-
"""测试版本管理 API"""

import requests
import os
import glob

BASE_URL = "http://localhost:8000/api/v1"

# 查找测试文件
FILES_DIR = "E:/Code/ai-teaching-ppt/uploads/generated"
ppt_files = glob.glob(os.path.join(FILES_DIR, "*.pptx"))
print(f"找到 PPT 文件：{len(ppt_files)} 个")

if not ppt_files:
    print("错误：未找到 PPTX 文件")
    exit(1)

PPT_A = ppt_files[0]
print(f"使用文件：{PPT_A}")

def test_create_session():
    """测试创建会话"""
    print("=" * 50)
    print("测试 1: 创建会话")
    print("=" * 50)

    with open(PPT_A, "rb") as f:
        r = requests.post(f"{BASE_URL}/ppt/session/create", files={"ppt_a": f})

    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Session ID: {data.get('session_id')}")
        print(f"Documents: {data.get('documents')}")
        return data.get('session_id')
    else:
        print(f"Error: {r.text}")
        return None

def test_get_session(session_id):
    """测试获取会话详情"""
    print("\n" + "=" * 50)
    print(f"测试 2: 获取会话详情 ({session_id})")
    print("=" * 50)

    r = requests.get(f"{BASE_URL}/ppt/session/{session_id}")
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Session: {data.get('session_id')}")
        for doc_id, doc in data.get('documents', {}).items():
            print(f"  {doc_id}: {len(doc.get('slides', {}))} 页")
    else:
        print(f"Error: {r.text}")

def test_toggle_slide(session_id):
    """测试删除/恢复页面"""
    print("\n" + "=" * 50)
    print("测试 3: 删除/恢复页面")
    print("=" * 50)

    payload = {
        "session_id": session_id,
        "document_id": "ppt_a",
        "slide_index": 0,
        "action": "delete"
    }
    r = requests.post(f"{BASE_URL}/ppt/slide/toggle", json=payload)
    print(f"删除 - Status: {r.status_code}, Response: {r.json()}")

    payload["action"] = "restore"
    r = requests.post(f"{BASE_URL}/ppt/slide/toggle", json=payload)
    print(f"恢复 - Status: {r.status_code}, Response: {r.json()}")

def test_version_history(session_id):
    """测试版本历史"""
    print("\n" + "=" * 50)
    print("测试 4: 获取版本历史")
    print("=" * 50)

    params = {
        "session_id": session_id,
        "document_id": "ppt_a",
        "slide_index": 0
    }
    r = requests.get(f"{BASE_URL}/ppt/session/{session_id}/history", params=params)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        versions = data.get('versions', [])
        print(f"版本数：{len(versions)}")
        for v in versions:
            print(f"  - {v.get('version')}: {v.get('operation')}")
    else:
        print(f"Error: {r.text}")

if __name__ == "__main__":
    # 测试创建会话
    session_id = test_create_session()

    if session_id:
        # 测试获取会话详情
        test_get_session(session_id)

        # 测试删除/恢复页面
        test_toggle_slide(session_id)

        # 测试版本历史
        test_version_history(session_id)

        print("\n" + "=" * 50)
        print("所有测试完成！")
        print("=" * 50)
