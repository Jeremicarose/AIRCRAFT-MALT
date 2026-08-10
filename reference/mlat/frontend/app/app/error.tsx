'use client';

import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Surface } from '@/components/ui/surface';

export default function ConsoleError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <main className="grid min-h-screen place-items-center bg-graphite-deep p-6"><Surface className="w-full max-w-md p-6 text-center"><div className="mx-auto flex size-10 items-center justify-center rounded-lg bg-failure/10 text-failure"><AlertTriangle className="size-5" /></div><h1 className="mt-4 text-lg font-semibold text-ink">Console data could not be loaded</h1><p className="mt-2 text-sm leading-6 text-ink-quiet">The operational API may be unavailable. Retry after confirming the environment connection.</p><Button variant="primary" className="mt-5" onClick={reset}><RefreshCw className="size-4" />Retry console</Button></Surface></main>;
}
