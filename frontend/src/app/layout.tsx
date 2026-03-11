import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Script from 'next/script'
import './globals.css'
import { Header } from '@/components/header'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AI 教学 PPT 生成器',
  description: '教师上传教材内容，AI 自动生成互动性强、美观的教学 PPT',
  icons: {
    icon: '/favicon.svg',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        {/* feat-171: pptxviewjs 依赖 - 使用 afterInteractive 在页面加载后加载 */}
        <Script src="/js/jszip.min.js" strategy="afterInteractive" />
        <Script src="/js/chart.umd.min.js" strategy="afterInteractive" />
        <Script src="/js/PptxViewJS.min.js" strategy="afterInteractive" />
        <div className="min-h-screen bg-gray-50">
          <Header />
          <main className="container mx-auto py-8">
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