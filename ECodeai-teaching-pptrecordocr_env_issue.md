# OCR 环境问题记录

**时间**: 2026-03-05
**问题**: 后端 OCR 引擎初始化失败 - No module named 'paddle'

**原因**: PaddlePaddle/PaddleOCR 未安装在后端环境中

**解决方案**:
1. 安装 PaddlePaddle: pip install paddlepaddle
2. 安装 PaddleOCR: pip install paddleocr
3. 验证：python -c "from paddleocr import PaddleOCR; print('OK')"

**影响**: 图片上传 OCR 功能暂时不可用，但文字输入模式正常
