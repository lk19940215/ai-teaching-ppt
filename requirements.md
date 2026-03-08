# api解析问题
- 目录：E:\Code\ai-teaching-ppt\uploads\generate
1. /api/v1/ppt/parse
   - test_ppt_b.pptx 
     - 结果：正常解析
     - 内容：
        ```
        {
            "success": true,
            "file_name": "test_parse.pptx",
            "file_size": 30056,
            "total_pages": 3,
            "enhanced": false,
            "pages": [
                {
                    "index": 1,
                    "title": "测试 PPT",
                    "content": [
                        "用于解析 API 测试"
                    ],
                    "shapes": [
                        {
                            "type": "placeholder",
                            "name": "Title 1",
                            "position": {
                                "x": 54,
                                "y": 167.75,
                                "width": 612,
                                "height": 115.75
                            },
                            "position_relative": {
                                "x": 7.5,
                                "y": 31.06,
                                "width": 85,
                                "height": 21.44
                            }
                        },
                        {
                            "type": "placeholder",
                            "name": "Subtitle 2",
                            "position": {
                                "x": 108,
                                "y": 306,
                                "width": 504,
                                "height": 138
                            },
                            "position_relative": {
                                "x": 15,
                                "y": 56.67,
                                "width": 70,
                                "height": 25.56
                            }
                        }
                    ],
                    "layout": {
                        "width": 720,
                        "height": 540
                    }
                },
                {
                    "index": 2,
                    "title": "第一页内容",
                    "content": [
                        "这是第一点\n这是第二点\n这是第三点"
                    ],
                    "shapes": [
                        {
                            "type": "placeholder",
                            "name": "Title 1",
                            "position": {
                                "x": 36,
                                "y": 21.62503937007874,
                                "width": 648,
                                "height": 90
                            },
                            "position_relative": {
                                "x": 5,
                                "y": 4,
                                "width": 90,
                                "height": 16.67
                            }
                        },
                        {
                            "type": "placeholder",
                            "name": "Content Placeholder 2",
                            "position": {
                                "x": 36,
                                "y": 126,
                                "width": 648,
                                "height": 356.37503937007875
                            },
                            "position_relative": {
                                "x": 5,
                                "y": 23.33,
                                "width": 90,
                                "height": 66
                            }
                        }
                    ],
                    "layout": {
                        "width": 720,
                        "height": 540
                    }
                },
                {
                    "index": 3,
                    "title": "第二页内容",
                    "content": [
                        "更多内容在这里"
                    ],
                    "shapes": [
                        {
                            "type": "placeholder",
                            "name": "Title 1",
                            "position": {
                                "x": 36,
                                "y": 21.62503937007874,
                                "width": 648,
                                "height": 90
                            },
                            "position_relative": {
                                "x": 5,
                                "y": 4,
                                "width": 90,
                                "height": 16.67
                            }
                        },
                        {
                            "type": "placeholder",
                            "name": "Content Placeholder 2",
                            "position": {
                                "x": 36,
                                "y": 126,
                                "width": 648,
                                "height": 356.37503937007875
                            },
                            "position_relative": {
                                "x": 5,
                                "y": 23.33,
                                "width": 90,
                                "height": 66
                            }
                        }
                    ],
                    "layout": {
                        "width": 720,
                        "height": 540
                    }
                }
            ],
            "parse_time_ms": 35,
            "from_cache": true
        }
        ```
   - 三角形的面积_0dc28a00.pptx
     - 结果：异常
     - 内容：
     ```
        {
            "detail": "PPT 解析失败：xmlns:ns2: '%s' is not a valid URI, line 2, column 86 (<string>, line 2)"
        }
     ```

# /merge PPT渲染方案调整
背景：调研了 3 个 Canvas 渲染 PPT 的 npm 包。推荐 PptxViewJS：Canvas 渲染、MIT 开源、TypeScript 支持、内置翻页 API
需求：替换 /merge页面PPT上传后，使用这个新包，用Canvas来渲染，这样才能看到真实的效果

# merge页面调用AI生成问题
- 接口：/api/v1/ppt/smart-merge-stream
- 以下是接口返回：
    ```
    data: {"stage": "uploading_files", "progress": 10, "message": "正在上传 PPT 文件..."}

    data: {"stage": "parsing_ppt", "progress": 25, "message": "正在解析 PPT 内容..."}

    data: {"stage": "generating_strategy", "progress": 50, "message": "正在调用 AI 生成合并策略..."}

    data: {"stage": "merging_ppt", "progress": 75, "message": "正在执行 PPT 合并..."}

    data: {"stage": "complete", "progress": 100, "message": "合并完成！", "result": {"success": true, "message": "智能合并成功", "download_url": "/uploads/generated/smart_merged_c682f794.pptx", "file_name": "smart_merged_c682f794.pptx", "strategy": {"slides_to_merge": [{"from_a": [2], "from_b": [2], "action": "combine", "instruction": "保留标题,正文合并,根据提示保留'123'内容,丢弃'123123'内容"}, {"from_a": [3], "from_b": [3], "action": "combine", "instruction": "保留标题,正文合并"}], "slides_to_skip_a": [1], "slides_to_skip_b": [1], "global_adjustments": "统一字体和颜色,根据全局提示'123'调整内容"}, "merged_from": ["test_ppt_b.pptx", "test_ppt_b.pptx"]}}
    ```
- 问题：
    5个流式返回，就输出内容，我觉得需要排查生成流程，确认是否调用了 第三方模型

特别声明：merge页面交互已经变更，请依据测试规则，生成相应的 任务。如果涉及 playwright mcp，参照示例来编写，特别涉及 SSE生成，强调 browser_wait_for 的多次调用，确保生成。还有就是文件上传，也有对应的工具。添加任务文件地址：E:\Code\ai-teaching-ppt\.claude-coder\tasks.json