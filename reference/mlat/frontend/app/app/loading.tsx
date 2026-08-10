import { Skeleton } from '@/components/ui/skeleton';

export default function ConsoleLoading() {
  return (
    <div className="flex min-h-screen bg-graphite-deep" role="status" aria-label="Loading console">
      <aside className="hidden w-[232px] shrink-0 border-r border-line bg-[#0b0e12] lg:block">
        <div className="flex h-16 items-center gap-3 border-b border-line px-3"><Skeleton className="size-8" /><div className="space-y-1.5"><Skeleton className="h-3 w-28" /><Skeleton className="h-2 w-20" /></div></div>
        <div className="space-y-6 p-3">{Array.from({ length: 4 }, (_, group) => <div key={group} className="space-y-2"><Skeleton className="h-2 w-14" /><Skeleton className="h-8 w-full" /><Skeleton className="h-8 w-5/6" /></div>)}</div>
      </aside>
      <div className="min-w-0 flex-1">
        <header className="flex h-16 items-center justify-between border-b border-line px-4 sm:px-6"><div className="space-y-2"><Skeleton className="h-4 w-28" /><Skeleton className="hidden h-2.5 w-64 sm:block" /></div><Skeleton className="h-8 w-48" /></header>
        <main className="space-y-4 p-4 sm:p-6">
          <div className="flex items-center justify-between rounded-lg border border-line bg-graphite p-5"><div className="flex items-center gap-4"><Skeleton className="size-10" /><div className="space-y-2"><Skeleton className="h-4 w-48" /><Skeleton className="h-2.5 w-72 max-w-[50vw]" /></div></div><Skeleton className="h-9 w-28" /></div>
          <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_330px]"><Skeleton className="h-[560px] rounded-lg border border-line" /><Skeleton className="h-[420px] rounded-lg border border-line" /></div>
          <Skeleton className="h-20 rounded-lg border border-line" />
        </main>
      </div>
      <span className="sr-only">Loading operational data</span>
    </div>
  );
}
