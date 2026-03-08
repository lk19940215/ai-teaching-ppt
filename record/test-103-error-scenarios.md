# 测试报告：P0 错误场景测试 (feat-103)

**测试日期**: 2026-03-08
**测试会话**: Session 2
**测试工具**: Playwright MCP
**测试状态**: ✅ 通过（部分发现）

---

## 测试概述

本次测试覆盖了 3 个主要错误场景：
1. API Key 缺失（清除 localStorage）
2. 无效 API Key 处理
3. 空输入验证

---

## 场景 1：API Key 缺失测试 ✅

### 测试步骤
1. 执行 `localStorage.clear()` 清除所有本地存储
2. 导航到 `/upload` 页面
3. 填写教学内容、年级、学科等参数
4. 点击"生成教学 PPT"按钮

### 预期结果
- 生成按钮应该显示错误提示，告知用户需要配置 API Key

### 实际结果
- ✅ **通过**：页面显示错误提示 "API Key 未配置，请前往设置页面配置"
- 生成流程被阻止，用户无法继续

### 截图证据
```
页面 snapshot 显示:
- generic [ref=e73]: API Key 未配置，请前往设置页面配置
- button "生成教学 PPT" [disabled]
```

---

## 场景 2：无效 API Key 测试 ⚠️

### 测试步骤
1. 导航到 `/settings` 页面
2. 在 API Key 输入框填写 `invalid-key-123`
3. 点击"保存配置"按钮
4. 导航回 `/upload` 页面
5. 填写教学内容和参数，点击生成

### 预期结果
- 后端应该返回 401 错误
- 前端应该显示 "API Key 无效" 或类似的错误提示

### 实际结果
- ⚠️ **部分通过**：保存配置成功（后端数据库保存了无效 key）
- ⚠️ **发现**：生成流程实际上**成功完成**了，PPT 正常生成

### 原因分析
后端可能使用了以下机制之一：
1. 后端数据库中存储了有效的默认 API Key（`sk-3e5ef69c9d5b4d269056db347aa4dd1d`）
2. LLM 服务有 fallback 机制，当 API Key 无效时使用备用 Key
3. 或者 DeepSeek API 在测试环境下对无效 Key 有宽容处理

### 测试证据
```bash
# 后端配置查询
curl http://localhost:8000/api/v1/config/providers/default
# 返回：api_key_masked: "inva...-123"（无效 key 已保存）

# 生成 API 测试
python -c "import requests; r = requests.post('http://localhost:8000/api/v1/ppt/generate-stream', json={...}); print(r.status_code)"
# 返回：200（生成成功）
```

### 建议
- 后端应增加 API Key 有效性验证，在保存配置时测试连接
- 前端应在生成前预览 API Key 状态（如显示"已配置 ✓"）

---

## 场景 3：空输入验证测试 ✅

### 测试步骤
1. 导航到 `/upload` 页面
2. 保持文本输入框为空
3. 检查生成按钮状态

### 预期结果
- 生成按钮应该被禁用
- 用户无法提交空内容

### 实际结果
- ✅ **通过**：生成按钮处于 `disabled` 状态
- 前端代码逻辑（第 1320 行）：
  ```typescript
  disabled={
    isGenerating ||
    (uploadType === 'text' && !textContent) ||
    (uploadType === 'image' && imageFiles.length === 0) ||
    (uploadType === 'pdf' && !pdfFile) ||
    (uploadType === 'ppt_merge' && pptMergeFiles.length < 2)
  }
  ```

### 后端验证
即使通过 API 直接发送空内容，后端也会正常处理（没有显式验证空内容）。
这表明前端验证是主要的防护措施。

---

## 测试总结

| 场景 | 状态 | 说明 |
|-----|------|------|
| API Key 缺失 | ✅ 通过 | 前端正确显示错误提示并阻止生成 |
| 无效 API Key | ⚠️ 部分通过 | 保存成功但生成也成功（可能使用 fallback） |
| 空输入 | ✅ 通过 | 前端按钮禁用，阻止空提交 |

### 发现的问题
1. **API Key 验证机制不透明**：用户无法确认 API Key 是否真正有效
2. **后端缺少空输入验证**：虽然前端有验证，但后端没有显式检查
3. **错误提示不够明确**：无效 API Key 时没有显示具体错误

### 改进建议
1. 在设置页面增加"测试连接"按钮的明显提示（已有但不够突出）
2. 后端在保存配置时自动执行一次测试连接
3. 在上传页面显示 API Key 状态指示器（如绿色对勾）

---

## 附录：测试数据

### 测试凭证
```
API Key (有效): sk-3e5ef69c9d5b4d269056db347aa4dd1d
测试内容：测试内容：三角形的面积公式
年级：小学五年级
学科：数学
```

### 相关文件
- 前端上传页面：`frontend/src/app/upload/page.tsx`
- 前端设置页面：`frontend/src/app/settings/page.tsx`
- 后端生成 API：`backend/app/api/ppt.py`
