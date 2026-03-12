# PPT 命名空间修复功能优化计划

## Context
某些 PPTX 文件包含无效的 XML 命名空间声明（如 `xmlns:ns2="%s"`），导致 python-pptx 解析失败。需要增强 `_fix_invalid_namespaces()` 函数的检测逻辑，并添加单元测试确保功能正常工作。

**问题发现**：代码中存在两个重复的 `_fix_invalid_namespaces` 函数：
- 模块级函数：第 79-151 行
- 嵌套函数（在 `parse_ppt` 内）：第 900-971 行

## 目标
1. 统一命名空间修复函数，消除重复代码
2. 确保正则表达式覆盖所有无效命名空间模式
3. 添加单元测试验证修复功能

---

## 实现步骤

### Step 1: 统一命名空间修复函数
**文件**: `backend/app/api/ppt.py`

**修改内容**:
1. 保留模块级函数 `_fix_invalid_namespaces()` (第 79-151 行)
2. 删除 `parse_ppt` 函数内的嵌套函数定义 (第 900-971 行)
3. 更新 `parse_ppt` 中的调用，直接使用模块级函数

**代码位置**:
- 删除: 第 900-971 行的嵌套函数定义
- 修改: 第 975 行 `temp_path = _fix_invalid_namespaces(temp_path)` 保持不变（自动使用模块级函数）

### Step 2: 验证正则表达式模式
**当前模式**（已实现）:
```python
# 模式1: 匹配 xmlns:ns\d+="%s" 或 xmlns:ns\d+='%s'
ns_pattern = re.compile(r'xmlns:ns(\d+)=([\'"])%s\2')

# 模式2: 匹配 xmlns:x="{.*}" 等包含 { 的占位符
placeholder_pattern = re.compile(r'xmlns:([a-zA-Z0-9_]+)=["\']\{([^}]*)\}[^"\']*["\']')
```

**状态**: 当前正则表达式已覆盖需求，无需修改。

### Step 3: 创建测试目录和测试文件
**目录结构**:
```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_ppt_namespace_fix.py
├── test_files/
│   └── 三角形的面积_0dc28a00.pptx  # 测试文件
```

**测试文件**: `backend/tests/test_ppt_namespace_fix.py`

```python
"""测试 PPTX 命名空间修复功能"""
import pytest
from pathlib import Path
from app.api.ppt import _fix_invalid_namespaces

class TestNamespaceFix:
    """命名空间修复测试类"""

    def test_fix_invalid_namespace_success(self, test_pptx_path):
        """测试修复无效命名空间成功"""
        # 调用修复函数
        fixed_path = _fix_invalid_namespaces(test_pptx_path)

        # 验证返回的路径存在
        assert fixed_path.exists()
        assert fixed_path.suffix == '.pptx'

        # 验证 PPTX 可以被解析
        from pptx import Presentation
        prs = Presentation(fixed_path)
        assert len(prs.slides) > 0

        # 清理
        if fixed_path != test_pptx_path:
            fixed_path.unlink()

    def test_parse_ppt_endpoint(self, client, test_pptx_path):
        """测试 PPT 解析接口"""
        with open(test_pptx_path, 'rb') as f:
            response = client.post(
                "/api/v1/ppt/parse",
                files={"file": (test_pptx_path.name, f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
                data={"extract_enhanced": False}
            )

        assert response.status_code == 200
        data = response.json()
        assert "pages" in data
        assert len(data["pages"]) > 0
```

**配置文件**: `backend/tests/conftest.py`

```python
"""测试配置和fixtures"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

@pytest.fixture
def test_pptx_path():
    """返回测试 PPTX 文件路径"""
    path = Path(__file__).parent.parent / "test_files" / "三角形的面积_0dc28a00.pptx"
    if not path.exists():
        pytest.skip(f"测试文件不存在: {path}")
    return path

@pytest.fixture
def client():
    """创建测试客户端"""
    from app.main import app
    return TestClient(app)
```

---

## 关键文件

| 文件 | 操作 |
|------|------|
| `backend/app/api/ppt.py` | 修改 - 删除嵌套函数定义 (第 900-971 行) |
| `backend/tests/__init__.py` | 新建 |
| `backend/tests/conftest.py` | 新建 |
| `backend/tests/test_ppt_namespace_fix.py` | 新建 |
| `backend/test_files/三角形的面积_0dc28a00.pptx` | 新建/复制测试文件 |

---

## 验证方案

1. **单元测试**
   ```bash
   cd backend
   pytest tests/test_ppt_namespace_fix.py -v
   ```

2. **手动验证**
   - 启动后端服务
   - 上传测试 PPTX 文件到 `/api/v1/ppt/parse` 接口
   - 验证返回的 `pages` 数量 > 0
   - 检查日志确认命名空间修复成功

3. **预期结果**
   - 文件能被成功解析
   - 不抛出 XML 解析异常
   - 日志显示修复的命名空间数量

---

## 风险评估
- **低风险**: 删除嵌套函数定义不影响其他功能
- **注意事项**: 确保测试文件 `三角形的面积_0dc28a00.pptx` 存在于 `backend/test_files/` 目录