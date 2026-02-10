import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Midnight Synth',
  description: 'LAN-controllable MIDI synthesizer workstation'
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang='en'>
      <body>{children}</body>
    </html>
  )
}
