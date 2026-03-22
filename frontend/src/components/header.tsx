import Link from "next/link"
import { Button } from "@/components/ui/button"

export function Header() {
  return (
    <header className="border-b bg-white sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link href="/merge" className="text-xl font-bold text-indigo-600">
            AI 教学 PPT
          </Link>
          <nav className="flex items-center gap-4">
            <Link href="/merge">
              <Button variant="ghost">合并</Button>
            </Link>
            <Link href="/generate">
              <Button variant="ghost">生成</Button>
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