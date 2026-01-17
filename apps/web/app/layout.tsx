import type { Metadata } from 'next'
import Link from 'next/link'
import './globals.css'
import { Button } from '@/components/ui/button'

export const metadata: Metadata = {
  title: 'Evolv - Your prompts, but smarter every week',
  description: 'Extract DNA from prompts, track mutations, understand lineage',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <nav className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
          <div className="container mx-auto px-4 py-3 sm:py-4">
            <div className="flex items-center justify-between">
              <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                <div className="p-1.5 sm:p-2 bg-blue-600 rounded-lg">
                  <svg className="h-4 w-4 sm:h-5 sm:w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <span className="text-lg sm:text-xl font-bold">Evolv</span>
              </Link>
              <div className="flex gap-1 sm:gap-2">
                <Link href="/logs">
                  <Button variant="ghost" size="sm" className="text-sm">Logs</Button>
                </Link>
                <Link href="/">
                  <Button variant="ghost" size="sm" className="text-sm">Home</Button>
                </Link>
              </div>
            </div>
          </div>
        </nav>
        {children}
      </body>
    </html>
  )
}
