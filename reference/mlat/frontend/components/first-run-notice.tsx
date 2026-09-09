'use client';

import { Info, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { buttonVariants } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const storageKey = 'receiver-registry-introduction-v2';

export function FirstRunNotice() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      setVisible(window.localStorage.getItem(storageKey) !== 'dismissed');
    } catch {
      setVisible(true);
    }
  }, []);

  const dismiss = () => {
    setVisible(false);
    try { window.localStorage.setItem(storageKey, 'dismissed'); } catch { /* Storage is optional. */ }
  };

  if (!visible) return null;

  return (
    <section aria-label="Getting started" className="mb-4 flex flex-col gap-4 rounded-md border border-signal-blue/30 bg-signal-blue/[0.06] p-4 sm:flex-row sm:items-center">
      <Info className="size-5 shrink-0 text-signal-blue" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <h2 className="text-sm font-semibold text-ink">A shared directory for independently owned receivers</h2>
        <p className="mt-1 max-w-3xl text-xs leading-5 text-ink-secondary">CKB keeps the same Type ID while metadata, status, or ownership changes. Coordinators can inspect and export the directory without connecting a wallet. MLAT is one reference consumer.</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <button type="button" onClick={dismiss} className={buttonVariants({ variant: 'primary', size: 'sm' })}>Dismiss guide</button>
        <button type="button" onClick={dismiss} className={cn(buttonVariants({ variant: 'ghost', size: 'icon-sm' }))} aria-label="Dismiss introduction"><X className="size-4" /></button>
      </div>
    </section>
  );
}
