import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AI 教学 PPT 生成器',
  description: '教师上传教材内容，AI 自动生成互动性强、美观的教学 PPT',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <div className="min-h-screen bg-background">
          <header className="border-b">
            <div className="container mx-auto px-4 py-4">
              <h1 className="text-2xl font-bold text-primary">AI 教学 PPT 生成器</h1>
              <p className="text-gray-600">上传教材内容，一键生成精美教学 PPT</p>
            </div>
          </header>
          <main className="container mx-auto px-4 py-8">
            {children}
          </main>
          <footer className="border-t mt-8 py-6 text-center text-gray-500 text-sm">
            <p>© 2026 AI 教学 PPT 生成器 - 助力教师高效备课</p>
          </footer>
        </div>
      </body>
    </html>
  )
}