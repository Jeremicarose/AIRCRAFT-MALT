'use client';

import dynamic from 'next/dynamic';
import type { ComponentProps } from 'react';
import type AirspaceMapComponent from '@/components/airspace-map';

const AirspaceMap = dynamic(() => import('@/components/airspace-map'), {
  ssr: false,
  loading: () => <div className="grid h-full min-h-[420px] place-items-center bg-[#090c10] text-xs text-ink-quiet">Loading airspace</div>,
});

export default function LazyAirspaceMap(props: ComponentProps<typeof AirspaceMapComponent>) {
  return <AirspaceMap {...props} />;
}
