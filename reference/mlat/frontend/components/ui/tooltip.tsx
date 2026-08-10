'use client';

import * as TooltipPrimitive from '@radix-ui/react-tooltip';
import type { ReactNode } from 'react';

export function Tooltip({ label, children, side = 'right' }: { label: string; children: ReactNode; side?: 'top' | 'right' | 'bottom' | 'left' }) {
  return (
    <TooltipPrimitive.Root>
      <TooltipPrimitive.Trigger asChild>{children}</TooltipPrimitive.Trigger>
      <TooltipPrimitive.Portal>
        <TooltipPrimitive.Content side={side} sideOffset={8} className="z-tooltip rounded-md bg-[#252b34] px-2 py-1.5 text-xs font-medium text-ink shadow-overlay motion-safe:animate-in motion-safe:fade-in">
          {label}
          <TooltipPrimitive.Arrow className="fill-[#252b34]" />
        </TooltipPrimitive.Content>
      </TooltipPrimitive.Portal>
    </TooltipPrimitive.Root>
  );
}
