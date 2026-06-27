import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Pipeline de Inovação | FIUS',
  description: 'Gestão do pipeline de inovação da Controladoria Jurídica · Finocchio & Ustra',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="bg-fius-light min-h-screen">{children}</body>
    </html>
  )
}
