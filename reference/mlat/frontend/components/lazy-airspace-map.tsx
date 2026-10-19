'use client';

import dynamic from 'next/dynamic';
import type { ComponentProps } from 'react';
import type AirspaceMapComponent from '@/components/airspace-map';
import { SectionErrorBoundary } from '@/components/section-error-boundary';

const AirspaceMap = dynamic(() => import('@/components/airspace-map'), {
  ssr: false,
  loading: () => <div className="grid h-full min-h-[420px] place-items-center bg-[#090c10] text-xs text-ink-quiet">Loading airspace</div>,
});

export default function LazyAirspaceMap(props: ComponentProps<typeof AirspaceMapComponent>) {
  return <SectionErrorBoundary title="Map unavailable" detail="The map component failed. Aircraft and receiver details outside the map are still available." resetKey={props.fitRequest ?? 0} diagnosticsHref="/app/environment"><AirspaceMap {...props} /></SectionErrorBoundary>;
}
