# -*- coding: utf-8 -*-
"""检查 API 端点"""
import requests

r = requests.get("http://localhost:8000/openapi.json")
if r.status_code == 200:
    data = r.json()
    paths = list(data.get('paths', {}).keys())
    print(f"总共 {len(paths)} 个端点")
    session_paths = [p for p in paths if 'session' in p or 'version' in p or 'slide' in p]
    print(f"\n版本管理相关端点 ({len(session_paths)} 个):")
    for p in session_paths:
        print(f"  {p}")
else:
    print(f"Error: {r.status_code}")
