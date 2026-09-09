import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function DataNotice({ title, detail, onRetry }: { title: string; detail: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-col gap-3 rounded-md border border-failure/35 bg-failure/[0.07] px-4 py-3 text-sm sm:flex-row sm:items-center">
      <AlertCircle className="size-4 shrink-0 text-failure" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <p className="font-semibold text-ink">{title}</p>
        <p className="mt-0.5 text-xs leading-5 text-ink-secondary">{detail}</p>
      </div>
      {onRetry ? <Button variant="secondary" size="sm" onClick={onRetry}><RefreshCw className="size-3.5" />Try again</Button> : null}
    </div>
  );
}
