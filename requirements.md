# 需求
阅读代码，处理以下问题。

## 以下是接口返回
/api/v1/ppt/ai-merge 调用，返回错误。
```
data: {"stage": "analysis", "progress": 25, "message": "正在解析 PPT B 内容..."}

data: {"stage": "thinking", "progress": 50, "message": "正在调用 AI 生成合并策略..."}

data: {"stage": "error", "progress": 0, "message": "AI 融合失败：sequence item 0: expected str instance, dict found"}
```

## 页面

```
内容摘要
添加标题内容
添加标题内容
个人信息：
工作简历：
```
其中，"添加标题内容"等内容，在解析、页面渲染的时候可以过滤掉。