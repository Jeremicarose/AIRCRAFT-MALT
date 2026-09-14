import { AlertCircle, CircleAlert, Info, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

type DataNoticeTone = 'failure' | 'attention' | 'neutral';

const toneStyles: Record<DataNoticeTone, { icon: typeof AlertCircle; root: string; iconColor: string }> = {
  failure: { icon: AlertCircle, root: 'border-failure/35 bg-failure/[0.07]', iconColor: 'text-failure' },
  attention: { icon: CircleAlert, root: 'border-attention/35 bg-attention/[0.06]', iconColor: 'text-attention' },
  neutral: { icon: Info, root: 'border-line bg-graphite-raised/55', iconColor: 'text-ink-quiet' },
};

export function DataNotice({
  title,
  detail,
  technicalDetail,
  tone = 'failure',
  onRetry,
}: {
  title: string;
  detail: string;
  technicalDetail?: string;
  tone?: DataNoticeTone;
  onRetry?: () => void;
}) {
  const presentation = toneStyles[tone];
  const Icon = presentation.icon;
  return (
    <div role={tone === 'failure' ? 'alert' : tone === 'attention' ? 'status' : undefined} className={cn('flex flex-col gap-3 rounded-md border px-4 py-3 text-sm sm:flex-row sm:items-start', presentation.root)}>
      <Icon className={cn('mt-0.5 size-4 shrink-0', presentation.iconColor)} aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <p className="font-semibold text-ink">{title}</p>
        <p className="mt-0.5 text-xs leading-5 text-ink-secondary">{detail}</p>
        {technicalDetail ? <details className="mt-2 text-[11px] text-ink-quiet"><summary className="w-fit cursor-pointer rounded-sm font-semibold outline-none hover:text-ink-secondary focus-visible:ring-2 focus-visible:ring-signal-blue">Technical details</summary><p className="mt-1 break-words font-mono leading-5">{technicalDetail}</p></details> : null}
      </div>
      {onRetry ? <Button variant="secondary" size="sm" onClick={onRetry}><RefreshCw className="size-3.5" />Try again</Button> : null}
    </div>
  );
}
