import type { Metadata } from 'next'
import Link from 'next/link'
import './globals.css'
import { Button } from '@/components/ui/button'
import Logo from '@/components/Logo'
import config from '@/config'
import { Toaster } from 'react-hot-toast'

export const metadata: Metadata = {
  title: config.metadata.title,
  description: config.metadata.description,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <Toaster position="top-right" />
        <nav className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50" aria-label="Main navigation">
          <div className="container mx-auto px-4 py-3 sm:py-4">
            <div className="flex items-center justify-between">
              <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity" aria-label={`${config.appName} home`}>
                <div className="p-1.5 sm:p-2 bg-blue-600 rounded-lg" aria-hidden="true">
                  <Logo className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
                </div>
                <span className="text-lg sm:text-xl font-bold">{config.appName}</span>
              </Link>
              <div className="flex gap-1 sm:gap-2" role="navigation" aria-label="Navigation links">
                {config.navLinks.map((link) => (
                  <Link key={link.href} href={link.href}>
                    <Button variant="ghost" size="sm" className="text-sm" aria-label={`Navigate to ${link.label}`}>
                      {link.label}
                    </Button>
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </nav>
        {children}
      </body>
    </html>
  )
}
