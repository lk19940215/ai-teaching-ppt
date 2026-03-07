# 图片上传有关

- 问题1：
OCR识别有问题，接口返回：
```
{
    "message": "OCR 识别成功",
    "text": "三角形的面积公式\n三角形的面积等于底乘以高除以二。\n公式：S=a×h÷2\n其中：\n-S表示面积\n-a表示底边长度\n-h表示底边上的高\n示例：\n一个底为6厘米、高为4厘米的三角形\n面积=6×4÷2=12平方厘米\n注意：底和高必须是对应的！",
    "char_count": 118
}
```

- 日志:
```
息: 用提供的模式无法找到文件。
E:\Code\ai-teaching-ppt\.venv\Lib\site-packages\paddle\utils\cpp_extension\extension_utils.py:711: UserWarning: No ccache found. Please be aware that recompiling all source files may be required. You can download and install ccache from: https://github.com/ccache/ccache/blob/master/doc/INSTALL.md
  warnings.warn(warning_message)
Creating model: ('PP-LCNet_x1_0_doc_ori', None)
Model files already exist. Using cached files. To redownload, please delete the directory manually: `C:\Users\LongKuo\.paddlex\official_models\PP-LCNet_x1_0_doc_ori`.
Creating model: ('UVDoc', None)
Model files already exist. Using cached files. To redownload, please delete the directory manually: `C:\Users\LongKuo\.paddlex\official_models\UVDoc`.
Creating model: ('PP-LCNet_x1_0_textline_ori', None)
Model files already exist. Using cached files. To redownload, please delete the directory manually: `C:\Users\LongKuo\.paddlex\official_models\PP-LCNet_x1_0_textline_ori`.
Creating model: ('PP-OCRv5_server_det', None)
Model files already exist. Using cached files. To redownload, please delete the directory manually: `C:\Users\LongKuo\.paddlex\official_models\PP-OCRv5_server_det`.
Creating model: ('PP-OCRv5_server_rec', None)
Model files already exist. Using cached files. To redownload, please delete the directory manually: `C:\Users\LongKuo\.paddlex\official_models\PP-OCRv5_server_rec`.
INFO:     127.0.0.1:6807 - "POST /api/v1/process/ocr HTTP/1.1" 200 OK
```

页面展示："图片 OCR 识别失败：未提取到有效文本"

- 问题2：
图片无法2次上传

# 其它想法（优先级底）
上传两个PPT，然后结合提示词，生成第3个PPT

# PPT动画、适配
目前生成的PPT，在下载后，出现文字超出页面，不换行等样式问题。如何处理，有没有成熟的方案




#