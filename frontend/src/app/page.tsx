export default function Home() {
  return (
    <div className="text-center py-12">
      <h2 className="text-4xl font-bold text-gray-800 mb-4">
        欢迎使用 AI 教学 PPT 生成器
      </h2>
      <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
        教师上传教材内容（拍照 / PDF / 文字），AI 自动生成互动性强、美观的教学 PPT。
        支持年级自适应、英语学科增强，生成的 .pptx 文件兼容 WPS Office。
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12">
        <div className="p-6 border rounded-xl shadow-sm">
          <div className="text-primary text-3xl mb-4">1</div>
          <h3 className="text-xl font-semibold mb-2">上传教材内容</h3>
          <p className="text-gray-600">
            支持拍照图片（OCR 识别）、PDF 电子书、直接粘贴文字三种方式输入教材内容。
          </p>
        </div>

        <div className="p-6 border rounded-xl shadow-sm">
          <div className="text-primary text-3xl mb-4">2</div>
          <h3 className="text-xl font-semibold mb-2">选择教学参数</h3>
          <p className="text-gray-600">
            选择年级、学科、PPT 风格和页数，AI 根据参数智能调整内容深度和表达方式。
          </p>
        </div>

        <div className="p-6 border rounded-xl shadow-sm">
          <div className="text-primary text-3xl mb-4">3</div>
          <h3 className="text-xl font-semibold mb-2">生成并下载 PPT</h3>
          <p className="text-gray-600">
            一键生成标准 .pptx 文件，可预览每页内容，下载后使用 WPS Office 直接编辑。
          </p>
        </div>
      </div>

      <div className="mt-12">
        <button className="bg-primary text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-primary/90 transition">
          开始使用
        </button>
        <p className="text-gray-500 mt-4">当前版本：开发中</p>
      </div>
    </div>
  )
}