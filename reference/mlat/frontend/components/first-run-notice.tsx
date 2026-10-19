'use client';

import { ArrowRight, Info, X } from 'lucide-react';
import Link from 'next/link';
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
    <section aria-label="Getting started" className="mb-4 flex flex-col gap-4 rounded-md border border-signal-blue/30 bg-signal-blue/[0.06] p-4 lg:flex-row lg:items-center">
      <Info className="size-5 shrink-0 text-signal-blue" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <h2 className="text-sm font-semibold text-ink">Registry identity is the first step, not proof of live operation</h2>
        <p className="mt-1 max-w-3xl text-xs leading-5 text-ink-secondary">CKB records a stable receiver identity, owner-authorized lifecycle, and declared metadata. MLAT separately checks discovery, feed availability, timing, and recent observations before a receiver can contribute.</p>
        <p className="mt-2 max-w-3xl text-xs leading-5 text-ink-quiet">CKB does not prove that hardware exists at the declared location, or that its clock and observation feed are accurate.</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <Link href="/app/receivers" className={buttonVariants({ variant: 'primary', size: 'sm' })}>Follow receiver readiness<ArrowRight className="size-4" /></Link>
        <button type="button" onClick={dismiss} className={cn(buttonVariants({ variant: 'ghost', size: 'icon-sm' }))} aria-label="Dismiss introduction"><X className="size-4" /></button>
      </div>
    </section>
  );
}
