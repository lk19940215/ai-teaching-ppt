from PIL import Image, ImageDraw, ImageFont

# 创建白色背景图片
img = Image.new('RGB', (800, 600), color='white')
draw = ImageDraw.Draw(img)

# 尝试加载中文字体
try:
    font = ImageFont.truetype('simhei.ttf', 28)
except:
    try:
        font = ImageFont.truetype('arial.ttf', 24)
    except:
        font = ImageFont.load_default()

# 文本内容
text = '''三角形的面积公式

三角形的面积等于底乘以高除以 2。

公式：S = a × h ÷ 2

示例：
底为 6 厘米、高为 4 厘米
面积 = 6 × 4 ÷ 2 = 12 平方厘米'''

# 绘制文本
draw.text((50, 50), text, fill='black', font=font)

# 保存图片
img.save('E:/Code/ai-teaching-ppt/record/test_image.png')
print('图片创建成功')
