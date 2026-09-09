'use client';

import { ccc } from '@ckb-ccc/connector-react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as Tooltip from '@radix-ui/react-tooltip';
import { useEffect, useState, type ReactNode } from 'react';
import { useOperatorStore } from '@/lib/operator-store';

const testnetClient = new ccc.ClientPublicTestnet();

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

  useEffect(() => {
    void Promise.resolve(useOperatorStore.persist.rehydrate()).finally(() => {
      useOperatorStore.getState().setHasHydrated(true);
    });
  }, []);

  return (
    <ccc.Provider name="CKB Receiver Registry" defaultClient={testnetClient}>
      <QueryClientProvider client={queryClient}>
        <Tooltip.Provider delayDuration={350}>{children}</Tooltip.Provider>
      </QueryClientProvider>
    </ccc.Provider>
  );
}
