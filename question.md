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