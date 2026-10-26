import type { ReactNode } from 'react';
import { AppShell } from '@/components/app-shell';

// The console frame survives navigation; only the workspace streams its next view.
// The shell's client queries load health independently, so a slow backend cannot
// block navigation or the local learning guide. Unknown is explicit until loaded.
export default function ConsoleLayout({ children }: { children: ReactNode }) {
  return <AppShell snapshot={{ modeData: null, healthData: null, aircraftData: null, receiverData: null }}>{children}</AppShell>;
}
