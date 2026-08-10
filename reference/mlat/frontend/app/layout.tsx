import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import Providers from '@/components/providers';
import './globals.css';

export const metadata: Metadata = {
  title: { default: 'MLAT Airspace Console', template: '%s | MLAT Airspace Console' },
  description: 'Aircraft tracking infrastructure with cryptographic proof.',
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body><Providers>{children}</Providers></body>
    </html>
  );
}
