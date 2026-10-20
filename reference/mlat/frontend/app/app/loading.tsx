import { Skeleton } from '@/components/ui/skeleton';

export default function ConsoleLoading() {
  return <section className="space-y-4" role="status" aria-label="Loading workspace" aria-busy="true">
    <div className="flex items-center gap-3 py-2 text-sm text-ink-secondary">
      <span aria-hidden="true" className="navigation-pending size-2 rounded-full bg-signal-blue" />
      Loading workspace. Navigation remains available.
    </div>
    <Skeleton className="h-20 w-full rounded-md" />
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
      <Skeleton className="h-96 rounded-md" />
      <Skeleton className="h-64 rounded-md" />
    </div>
  </section>;
}
