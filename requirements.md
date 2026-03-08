# 问题分析与解决方案计划

## 背景

用户提到 @requirements.md 中的需求已编排到 @.claude-coder/tasks.json，但实际再次运行时**问题仍然存在**。这表明之前的任务虽然标记为 "done"，但实际执行并未真正解决问题。

## 问题诊断

根据 requirements.md 和现有代码分析，发现以下**真实问题**：

### 问题 1: XML 解析错误未完全解决
**症状**: `三角形的面积_0dc28a00.pptx` 解析失败，错误信息：
```
PPT 解析失败：xmlns:ns2: '%s' is not a valid URI, line 2, column 86
```

**当前状态**:
- `backend/app/api/ppt.py` 中的 `parse_ppt()` 路由已添加 `_fix_invalid_namespaces()` 函数（第 823-889 行）
- 但该函数**仅在特定条件下触发**：检测到 `xmlns:ns2="%s"` 或 `xmlns:ns3="%s"` 时才会执行修复
- `三角形的面积_0dc28a00.pptx` 文件可能包含**其他变体的无效命名空间**（如 `xmlns:ns4="%s"` 等），导致修复未生效

**根本原因**:
1. 命名空间修复逻辑不完整，只匹配有限的 ns2/ns3 模式
2. 预检逻辑（第 830-841 行）可能遗漏某些无效命名空间变体
3. 缺少实际测试验证：虽然 tasks.json 中记录 "测试验证通过"，但实际运行时问题重现

### 问题 2: /merge 流程测试记录与实际不符
**症状**: 用户再次运行时发现问题仍存在

**当前状态**:
- tasks.json 中 feat-209 标记为 "done"，测试报告 `record/merge-e2e-20260308.md` 显示 "PASS"
- 但测试报告第 71 行备注：**"合并流程执行非常快（约 2-3 秒），可能使用了缓存或 LLM fallback 机制"**
- 这暗示测试可能没有真正调用第三方 LLM API

**根本原因**:
1. 测试报告中提到 "后端日志显示返回了完整的策略 JSON"，但**未验证是否真实调用第三方 LLM**
2. 流程过快（2-3 秒）不符合真实 LLM 调用耗时（通常 10-60 秒）
3. 可能使用了缓存或 mock 机制，而非真实调用

### 问题 3: AI 调用真实性验证不充分
**症状**: 用户要求 "确认是否调用了第三方模型"

**当前状态**:
- `feat-207` 标记为 "done"，声称验证了 LLM 真实调用
- 但 tasks.json notes 仅提到 "从 LLM 返回的完整结构化 JSON 可以确认真调用成立"
- **未提供关键证据**：如 API 调用日志、token 消耗记录、第三方服务响应时间

**根本原因**:
1. 后端代码中虽然有日志（第 1611 行：`logger.info(f"✅ LLM 响应成功，耗时 {llm_elapsed:.1f}s")`）
2. 但**没有记录 API 请求详情**：请求时间戳、provider、tokens 使用、响应内容摘要
3. 缺少第三方服务返回的唯一标识（如 request_id、usage 信息）

---

## 解决方案计划

### 阶段 1: 修复 XML 解析错误（P0）

**目标**: 确保所有包含无效 XML 命名空间的 PPTX 文件都能被正确解析

**步骤**:

1. **增强命名空间检测逻辑**
   - 修改 `_fix_invalid_namespaces()` 函数，使用更通用的正则表达式
   - 匹配模式从 `xmlns:ns2="%s"` 和 `xmlns:ns3="%s"` 扩展到所有 `xmlns:ns\d+="%s"`
   - 同时处理其他可能的无效占位符，如 `xmlns:.*="{.*}.*"`

2. **简化预检逻辑，改为全面扫描**
   - 移除快速预检（第 830-841 行）
   - 直接解压扫描所有 XML 文件，修复所有无效命名空间
   - 添加日志记录：修复了多少文件、替换了哪些命名空间

3. **添加测试用例**
   - 使用 `三角形的面积_0dc28a00.pptx` 作为测试文件
   - 编写单元测试验证修复功能
   - 验证点：
     - 文件能被成功解析
     - 返回的 pages 数量 > 0
     - 不抛出 XML 解析异常

**影响文件**:
- `backend/app/api/ppt.py` (第 823-889 行 `_fix_invalid_namespaces()` 函数)

---

### 阶段 2: 验证 AI 真实调用（P0）

**目标**: 100% 确认智能合并流程真实调用第三方 LLM API，而非使用缓存/mock

**步骤**:

1. **增强后端日志**
   - 在 `smart_merge_ppt_stream()` 中添加详细日志：
     - LLM 请求发送时间
     - Provider 和模型名称
     - Request tokens / Response tokens 使用情况
     - 第三方服务返回的唯一 request_id（如有）
     - API 调用实际耗时（不包括网络延迟）

2. **清除缓存强制真实调用**
   - 临时禁用 PPT 解析缓存（`use_cache=False`）
   - 如果存在策略生成缓存，也临时禁用
   - 确保每次测试都是全新的 LLM 调用

3. **手动验证流程**
   - 启动后端服务：`cd backend && uvicorn app.main:app --reload --port 8000`
   - **实时监控日志**：`tail -f backend/logs/uvicorn.log`
   - 前端上传两个测试 PPT，触发合并
   - 检查日志中是否包含：
     - `LLM 请求发送: provider=deepseek, model=xxx`
     - `Tokens 使用: prompt_tokens=X, completion_tokens=Y, total_tokens=Z`
     - `LLM 响应耗时: XX.Xs`
     - `策略 JSON: {...}`（完整策略内容）

4. **检查第三方服务账单/调用记录**
   - 登录 DeepSeek/OpenAI/Claude 后台
   - 查看测试时间段的 API 调用记录
   - 确认 token 消耗与日志记录一致

5. **记录验证证据**
   - 截图日志中的关键信息
   - 记录第三方服务的调用记录
   - 更新测试报告，标注真实调用证据

**影响文件**:
- `backend/app/api/ppt.py` (第 1361-2200 行 `smart_merge_ppt_stream()`)
- `backend/logs/uvicorn.log` (日志文件)

---

### 阶段 3: 更新任务编排（P1）

**目标**: 将真实问题和解决方案更新到 tasks.json，确保任务状态与实际情况一致

**步骤**:

1. **重新评估现有任务状态**
   - `feat-115` (XML 解析错误): 从 "done" 改为 "in_progress"
   - `feat-207` (AI 调用验证): 从 "done" 改为 "in_progress"
   - `feat-209` (/merge 测试): 从 "done" 改为 "in_progress"

2. **添加新的子任务**
   - feat-301: XML 命名空间通用修复（阶段 1 完整实现）
   - feat-302: LLM 调用日志增强（阶段 2 步骤 1）
   - feat-303: 真实调用验证测试（阶段 2 步骤 2-5）
   - feat-304: 任务状态同步更新

3. **更新测试报告**
   - 更新 `record/merge-e2e-20260308.md`
   - 重新运行测试并记录真实结果
   - 标注验证证据（日志截图、第三方服务记录）

**影响文件**:
- `.claude-coder/tasks.json`
- `record/merge-e2e-20260308.md`

---

## 验证标准

### XML 解析修复验证
- [ ] `三角形的面积_0dc28a00.pptx` 能被成功解析
- [ ] 返回的 `pages` 数组长度 > 0（原文件应返回 9 页）
- [ ] 不抛出任何 XML 解析异常
- [ ] 日志中显示修复了命名空间（如 "修复了 3 个 XML 文件中的无效命名空间"）

### AI 调用真实性验证
- [ ] 后端日志包含完整的 LLM 调用记录（请求 + 响应）
- [ ] 记录了真实的 token 使用情况（不为 0）
- [ ] 第三方服务后台显示对应的 API 调用
- [ ] 调用耗时符合预期（通常 10-60 秒，而非 2-3 秒）
- [ ] 清除缓存后仍能获得相同或类似的策略结果

### 任务编排更新验证
- [ ] tasks.json 中所有相关任务状态更新为真实情况
- [ ] 添加新的子任务（feat-301~304）
- [ ] 更新的测试报告包含验证证据

---

## 任务编排（更新到 tasks.json）

```json
{
  "id": "feat-301",
  "category": "bugfix",
  "priority": 301,
  "description": "P0 XML 命名空间通用修复：支持所有 ns%d 变体",
  "steps": [
    "【修复】修改 _fix_invalid_namespaces() 正则表达式：匹配 xmlns:ns\\d+=\"%s\"",
    "【修复】移除快速预检，改为全面扫描所有 XML 文件",
    "【增强】添加日志：记录修复的文件数和命名空间",
    "【测试】使用 三角形的面积_0dc28a00.pptx 验证解析成功",
    "【验证】返回 pages.length > 0，无 XML 异常"
  ],
  "status": "pending",
  "depends_on": []
}

{
  "id": "feat-302",
  "category": "feature",
  "priority": 302,
  "description": "P0 LLM 调用日志增强：记录真实 token 使用和耗时",
  "steps": [
    "【增强】smart_merge_ppt_stream() 添加 LLM 请求日志：provider、model、timestamp",
    "【增强】记录 tokens 使用：prompt_tokens、completion_tokens、total_tokens",
    "【增强】记录第三方 request_id（如有）",
    "【增强】记录真实 API 调用耗时（不包括网络）",
    "【验证】日志中显示非零的 token 使用和 10-60s 耗时"
  ],
  "status": "pending",
  "depends_on": []
}

{
  "id": "feat-303",
  "category": "test",
  "priority": 303,
  "description": "P0 真实调用验证：清除缓存 + 第三方服务记录",
  "steps": [
    "【环境】启动后端：cd backend && uvicorn app.main:app --reload --port 8000",
    "【环境】清除缓存：rm backend/logs/*.log; touch backend/logs/uvicorn.log",
    "【P0】实时监控日志：tail -f backend/logs/uvicorn.log",
    "【P0】浏览器访问 http://localhost:3000/merge",
    "【P0】上传两个测试 PPT（test_ppt_b.pptx），确认预览正确",
    "【P0】点击合并，观察日志中的 LLM 调用记录",
    "【验证】日志包含：provider、tokens、耗时、策略 JSON",
    "【验证】第三方服务后台显示对应调用记录",
    "【记录】截图日志和第三方服务记录，更新测试报告"
  ],
  "status": "pending",
  "depends_on": [
    "feat-302"
  ]
}

{
  "id": "feat-304",
  "category": "maintenance",
  "priority": 304,
  "description": "P1 任务状态同步更新",
  "steps": [
    "【更新】feat-115 状态从 done 改为 completed（修复确认）",
    "【更新】feat-207 状态从 done 改为 completed（验证确认）",
    "【更新】feat-209 状态从 done 改为 completed（测试确认）",
    "【添加】feat-301、feat-302、feat-303 三个新任务",
    "【更新】测试报告 record/merge-e2e-20260308.md 包含真实证据"
  ],
  "status": "pending",
  "depends_on": [
    "feat-301",
    "feat-303"
  ]
}
```

分析上面的内容，采用正确的格式添加任务。