import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import Providers from '@/components/providers';
import './globals.css';

export const metadata: Metadata = {
  title: { default: 'CKB Receiver Registry', template: '%s | CKB Receiver Registry' },
  description: 'Manage stable receiver identities and verify owner-authorized lifecycle history on CKB testnet.',
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body><Providers>{children}</Providers></body>
    </html>
  );
}
