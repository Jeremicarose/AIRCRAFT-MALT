'use client';

import dynamic from 'next/dynamic';
import type { ComponentProps } from 'react';
import type { DistributionChart as DistributionChartType, MultiLineChart as MultiLineChartType, Sparkline as SparklineType, TrendChart as TrendChartType } from '@/components/charts';

const loading = () => <div className="h-full w-full animate-pulse rounded-md bg-[linear-gradient(90deg,rgba(20,24,30,0.9),rgba(34,40,48,0.88),rgba(20,24,30,0.9))]" />;

const LazyTrendChart = dynamic(() => import('@/components/charts').then((module) => module.TrendChart), { ssr: false, loading });
const LazyMultiLineChart = dynamic(() => import('@/components/charts').then((module) => module.MultiLineChart), { ssr: false, loading });
const LazyDistributionChart = dynamic(() => import('@/components/charts').then((module) => module.DistributionChart), { ssr: false, loading });
const LazySparkline = dynamic(() => import('@/components/charts').then((module) => module.Sparkline), { ssr: false, loading });

export function TrendChart({ height = 220, ...props }: ComponentProps<typeof TrendChartType>) {
  return <div style={{ height }} className="w-full"><LazyTrendChart {...props} height={height} /></div>;
}

export function MultiLineChart({ height = 240, ...props }: ComponentProps<typeof MultiLineChartType>) {
  return <div style={{ height }} className="w-full"><LazyMultiLineChart {...props} height={height} /></div>;
}

export function DistributionChart({ height = 220, ...props }: ComponentProps<typeof DistributionChartType>) {
  return <div style={{ height }} className="w-full"><LazyDistributionChart {...props} height={height} /></div>;
}

export function Sparkline(props: ComponentProps<typeof SparklineType>) {
  return <div className="h-9 w-24"><LazySparkline {...props} /></div>;
}
