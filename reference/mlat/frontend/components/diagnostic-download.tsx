'use client';

import { Download } from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { fetchJson } from '@/lib/api';
import { useMissionStore } from '@/lib/mission-store';

export function DiagnosticDownload() {
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState('');
  const [failed, setFailed] = useState(false);
  const download = async () => {
    setPending(true); setMessage(''); setFailed(false);
    try {
      const report = await fetchJson<Record<string, unknown>>('/api/diagnostics/bundle');
      if (!report || report.schema_version !== 1 || !report.source_context || !Array.isArray(report.receivers)) throw new Error('Invalid report');
      const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2) + '\n'], { type: 'application/json' }));
      const link = document.createElement('a');
      link.href = url; link.download = 'mlat-diagnostics.json';
      document.body.appendChild(link);
      try { link.click(); } finally { link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
      useMissionStore.getState().complete('diagnostics');
      setMessage('Report prepared for download. Review it before sharing.');
    } catch {
      setFailed(true);
      setMessage('The diagnostic report could not be downloaded. Check the service and try again.');
    } finally { setPending(false); }
  };
  return <div className="max-w-sm text-right"><Button size="sm" variant="secondary" disabled={pending} onClick={() => void download()}><Download className="size-3.5" />{pending ? 'Preparing diagnostics…' : 'Export diagnostics'}</Button><p role="status" className={`mt-1 text-xs leading-5 ${failed ? 'text-attention' : 'text-ink-secondary'}`}>{message}</p></div>;
}
