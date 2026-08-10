'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as Tooltip from '@radix-ui/react-tooltip';
import { useState, type ReactNode } from 'react';

export default function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        refetchOnWindowFocus: false,
        retry: 1,
        staleTime: 5_000,
      },
    },
  }));

  return (
    <QueryClientProvider client={queryClient}>
      <Tooltip.Provider delayDuration={350}>{children}</Tooltip.Provider>
    </QueryClientProvider>
  );
}
