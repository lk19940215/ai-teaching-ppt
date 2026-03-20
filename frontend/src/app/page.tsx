/**
 * 根页面 - 自动重定向到 /merge
 */
import { redirect } from 'next/navigation'

export default function HomePage() {
  redirect('/merge')
}