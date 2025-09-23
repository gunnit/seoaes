import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AIVisibility.pro - AI Search Optimization Platform',
  description: 'Discover why your website doesn\'t appear in AI search results. Get instant analysis and actionable fixes for ChatGPT, Perplexity, and Claude visibility.',
  keywords: 'AI SEO, ChatGPT optimization, AI visibility, LLM optimization, AI search',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}