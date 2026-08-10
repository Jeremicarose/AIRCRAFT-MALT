'use client';

import { Area, AreaChart, Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useId } from 'react';
import { useReducedMotion } from 'framer-motion';

type ChartRow = Record<string, string | number | boolean | null>;

const tooltipStyle = { background: '#11151a', border: '1px solid #2a3039', borderRadius: 6, color: '#f1f4f8', fontSize: 11 };

export function TrendChart({ data, dataKey, color = '#5b9cff', unit = '', height = 220, ariaLabel }: { data: ChartRow[]; dataKey: string; color?: string; unit?: string; height?: number; ariaLabel?: string }) {
  const reduceMotion = useReducedMotion();
  const gradientId = `fill-${useId().replaceAll(':', '')}`;
  return <div style={{ height }} className="w-full" role="img" aria-label={ariaLabel ?? `${dataKey.replaceAll('_', ' ')} trend`}><ResponsiveContainer width="100%" height="100%"><AreaChart data={data} margin={{ top: 12, right: 12, left: -18, bottom: 0 }}><defs><linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={color} stopOpacity={0.22} /><stop offset="100%" stopColor={color} stopOpacity={0} /></linearGradient></defs><CartesianGrid vertical={false} strokeDasharray="2 4" /><XAxis dataKey="label" axisLine={false} tickLine={false} minTickGap={24} /><YAxis axisLine={false} tickLine={false} width={52} tickFormatter={(value) => `${value}${unit}`} /><Tooltip contentStyle={tooltipStyle} formatter={(value) => [`${value}${unit}`, dataKey.replaceAll('_', ' ')]} /><Area type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} fill={`url(#${gradientId})`} isAnimationActive={!reduceMotion} animationDuration={180} /></AreaChart></ResponsiveContainer></div>;
}

export function MultiLineChart({ data, series, height = 240, ariaLabel }: { data: ChartRow[]; series: Array<{ key: string; color: string; label: string }>; height?: number; ariaLabel?: string }) {
  const reduceMotion = useReducedMotion();
  return <div style={{ height }} className="w-full" role="img" aria-label={ariaLabel ?? `${series.map((item) => item.label).join(' and ')} trends`}><ResponsiveContainer width="100%" height="100%"><LineChart data={data} margin={{ top: 12, right: 16, left: -18, bottom: 0 }}><CartesianGrid vertical={false} strokeDasharray="2 4" /><XAxis dataKey="label" axisLine={false} tickLine={false} minTickGap={24} /><YAxis axisLine={false} tickLine={false} width={52} /><Tooltip contentStyle={tooltipStyle} />{series.map((item) => <Line key={item.key} type="monotone" dataKey={item.key} name={item.label} stroke={item.color} strokeWidth={2} dot={false} isAnimationActive={!reduceMotion} animationDuration={180} />)}</LineChart></ResponsiveContainer></div>;
}

export function DistributionChart({ data, dataKey, color = '#4bb6a3', height = 220, ariaLabel }: { data: ChartRow[]; dataKey: string; color?: string; height?: number; ariaLabel?: string }) {
  const reduceMotion = useReducedMotion();
  return <div style={{ height }} className="w-full" role="img" aria-label={ariaLabel ?? `${dataKey.replaceAll('_', ' ')} distribution`}><ResponsiveContainer width="100%" height="100%"><BarChart data={data} margin={{ top: 12, right: 12, left: -18, bottom: 0 }}><CartesianGrid vertical={false} strokeDasharray="2 4" /><XAxis dataKey="label" axisLine={false} tickLine={false} /><YAxis axisLine={false} tickLine={false} width={52} /><Tooltip contentStyle={tooltipStyle} /><Bar dataKey={dataKey} fill={color} radius={[3, 3, 0, 0]} isAnimationActive={!reduceMotion} animationDuration={180} /></BarChart></ResponsiveContainer></div>;
}

export function Sparkline({ data, dataKey, color = '#5b9cff' }: { data: ChartRow[]; dataKey: string; color?: string }) {
  return <div className="h-9 w-24"><ResponsiveContainer width="100%" height="100%"><LineChart data={data}><Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={1.75} dot={false} isAnimationActive={false} /></LineChart></ResponsiveContainer></div>;
}
