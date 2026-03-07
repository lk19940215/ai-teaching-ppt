from app.services.llm import LLMService
import json

llm = LLMService()

# 模拟 LLM 返回的带 markdown 的 JSON
test_response = """```json
{
  "slides_to_merge": [
    {
      "from_a": [2],
      "from_b": [],
      "action": "append_a",
      "instruction": "test"
    }
  ],
  "slides_to_skip_a": [1],
  "slides_to_skip_b": [1],
  "global_adjustments": "test"
}
```"""

print('Original response:')
print(test_response)
print()

extracted = llm._extract_json_from_response(test_response)
print('Extracted JSON:')
print(extracted)
print()

fixed = llm._fix_json(extracted)
print('Fixed JSON:')
print(fixed)
print()

try:
    parsed = json.loads(fixed)
    print('JSON parsed successfully!')
    print(parsed)
except Exception as e:
    print(f'JSON parse failed: {e}')
