# -*- coding: utf-8 -*-
"""检查 API 端点 - 打印所有路径"""
import requests

r = requests.get("http://localhost:8000/openapi.json")
if r.status_code == 200:
    data = r.json()
    paths = sorted(data.get('paths', {}).keys())
    print(f"总共 {len(paths)} 个端点:\n")
    for p in paths:
        print(f"  {p}")
else:
    print(f"Error: {r.status_code} - {r.text[:200]}")
