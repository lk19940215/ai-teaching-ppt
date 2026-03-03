import Link from "next/link"
import { Button } from "@/components/ui/button"

export function Header() {
  return (
    <header className="border-b bg-white sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-indigo-600">
            AI 教学 PPT 生成器
          </Link>
          <nav className="flex items-center gap-4">
            <Link href="/">
              <Button variant="ghost">首页</Button>
            </Link>
            <Link href="/upload">
              <Button variant="ghost">生成 PPT</Button>
            </Link>
            <Link href="/history">
              <Button variant="ghost">历史记录</Button>
            </Link>
            <Link href="/settings">
              <Button variant="ghost">设置</Button>
            </Link>
          </nav>
        </div>
      </div>
    </header>
  )
}