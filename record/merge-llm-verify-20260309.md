# AI 真实调用验证测试报告

**日期**: 2026-03-09 | **环境**: 前端 http://localhost:3000 / 后端 http://localhost:8000

## 测试目标

验证 feat-307 "P0 AI 真实调用验证：第三方服务后台记录 + 日志增强"

## 测试结果

| 场景 | 结果 | 备注 |
|------|------|------|
| PPT 上传 | PASS | 两个 PPT 文件成功上传并解析（A: 3 页，B: 8 页） |
| Canvas 预览 | PASS | Canvas 渲染正常，页面计数正确 |
| 合并按钮点击 | PASS | 按钮状态正确变为"合并中..." |
| SSE 进度推送 | PARTIAL | 能收到"正在上传 PPT 文件..."(10%) 和"正在解析 PPT 内容..."(25%) 事件 |
| LLM 调用 | FAIL | 在 calling_llm 阶段报错：Connection error |

## 问题分析

### 症状
- 前端显示："智能合并失败：LLM API 错误：Connection error."
- SSE 流在 stage="calling_llm", progress=50% 后返回 error 事件
- 直接 Python 脚本调用 DeepSeek API 成功（tokens used: 16）
- uvicorn 进程监听 8000 端口，健康检查通过

### 诊断步骤
1. ✅ 验证 API Key 有效性：Python 脚本直接调用成功
2. ✅ 验证后端服务运行：curl http://localhost:8000/health 返回 {"status":"healthy"}
3. ✅ 验证前端配置：localStorage.llm_config 正确配置 deepseek provider
4. ✅ 验证请求发送：SSE 流能收到前两个阶段事件
5. ❌ LLM 调用失败：uvicorn 进程内调用失败

### 可能原因
1. **uvicorn 进程网络隔离**：多个 uvicorn --reload 进程（PID: 17784, 9272, 18184, 14384, 2028, 17752）可能导致网络状态异常
2. **进程杀不掉**：npx kill-port 和 taskkill 都无法完全停止这些进程
3. **环境变量问题**：uvicorn 进程可能使用了不同的 Python 环境或网络代理设置

### 已尝试的修复
1. 重启后端服务（多次）
2. 清除 localStorage 并重新配置 LLM
3. 使用不同提示语测试（中文/英文）
4. 直接 Python 脚本测试 API（成功）

## 代码分析

### 后端日志点（backend/app/api/ppt.py:1698-1701）
```python
except Exception as e:
    llm_elapsed = _time.time() - llm_start_time
    logger.error(f"❌ LLM chat 失败（耗时 {llm_elapsed:.1f}s）：{type(e).__name__}: {e}", exc_info=True)
    raise
```

### LLM 服务错误包装（backend/app/services/llm.py:148-150）
```python
except Exception as e:
    logger.error(f"LLM 调用失败：{e}")
    raise RuntimeError(f"LLM 调用失败：{e}") from e
```

"Connection error" 来自 openai 库的原始异常消息。

## 下一步建议

1. **完全停止 uvicorn 进程**：找到方法彻底停止所有监听 8000 端口的进程
2. **冷启动后端**：在无其他进程干扰的情况下启动单个 uvicorn 实例
3. **添加调试日志**：在 LLM 调用前输出 api_key、provider、base_url 等参数
4. **检查防火墙/代理**：确认 uvicorn 进程的网络访问权限

## 附录：测试命令

```bash
# 直接 Python 测试（成功）
python -c "
from openai import OpenAI
client = OpenAI(api_key='sk-3e5ef69c9d5b4d269056db347aa4dd1d', base_url='https://api.deepseek.com')
response = client.chat.completions.create(
    model='deepseek-chat',
    messages=[{'role': 'user', 'content': 'Say hi'}],
    max_tokens=10,
    timeout=30
)
print('API call successful, tokens used:', response.usage.total_tokens)
"

# 后端健康检查
curl -s http://localhost:8000/health
```

## 结论

**测试状态**: FAILED

**根因**: uvicorn 进程网络访问异常（疑似多进程 --reload 导致的状态问题）

**影响**: 无法验证 AI 真实调用（因为 LLM API 调用失败）

**建议**: 需要系统管理员协助彻底停止 uvicorn 进程并冷启动
