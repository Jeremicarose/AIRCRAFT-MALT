'use client';

import { flexRender, getCoreRowModel, getSortedRowModel, useReactTable, type ColumnDef, type Row, type SortingState } from '@tanstack/react-table';
import { useVirtualizer } from '@tanstack/react-virtual';
import { ArrowDown, ArrowUp, ChevronsUpDown } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { cn } from '@/lib/utils';

interface DataGridProps<T> {
  data: T[];
  columns: ColumnDef<T, any>[];
  getRowId?: (row: T) => string;
  onRowClick?: (row: T) => void;
  isRowSelected?: (row: T) => boolean;
  emptyLabel?: string;
  height?: number;
  ariaLabel?: string;
  keyboardColumnLabel?: (row: T) => string;
}

export function DataGrid<T>({ data, columns, getRowId, onRowClick, isRowSelected, emptyLabel = 'No records available.', height = 540, ariaLabel = 'Data table', keyboardColumnLabel }: DataGridProps<T>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [rowHeight, setRowHeight] = useState(46);
  const [focusedRowIndex, setFocusedRowIndex] = useState(0);
  const parentRef = useRef<HTMLDivElement>(null);
  const table = useReactTable({ data, columns, getRowId, state: { sorting }, onSortingChange: setSorting, getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel() });
  const rows = table.getRowModel().rows;
  const virtualizer = useVirtualizer({ count: rows.length, getScrollElement: () => parentRef.current, estimateSize: () => rowHeight, overscan: 10 });

  useEffect(() => {
    const loadDensity = () => {
      try {
        const stored = document.documentElement.dataset.compactRows;
        if (stored === 'true' || stored === 'false') {
          setRowHeight(stored === 'true' ? 38 : 46);
          return;
        }
        const preferences = JSON.parse(window.localStorage.getItem('mlat-console-preferences') ?? '{}') as { compactRows?: boolean };
        document.documentElement.dataset.compactRows = preferences.compactRows ? 'true' : 'false';
        setRowHeight(preferences.compactRows ? 38 : 46);
      } catch {
        setRowHeight(46);
      }
    };
    loadDensity();
    window.addEventListener('mlat-preferences-change', loadDensity);
    return () => window.removeEventListener('mlat-preferences-change', loadDensity);
  }, []);

  useEffect(() => {
    if (!rows.length) {
      setFocusedRowIndex(0);
      return;
    }
    setFocusedRowIndex((current) => Math.min(current, rows.length - 1));
  }, [rows.length]);

  const handleKeyboardSelection = (index: number) => {
    setFocusedRowIndex(index);
    virtualizer.scrollToIndex(index, { align: 'auto' });
  };

  return (
    <div role="table" aria-label={ariaLabel} aria-rowcount={rows.length} className="min-w-0 overflow-hidden">
      <div role="rowgroup" className="border-b border-line bg-graphite-raised/55">
        {table.getHeaderGroups().map((headerGroup) => (
          <div key={headerGroup.id} role="row" className="flex h-10 items-center">
            {headerGroup.headers.map((header) => {
              const sorted = header.column.getIsSorted();
              return (
                <button key={header.id} role="columnheader" aria-sort={sorted === 'asc' ? 'ascending' : sorted === 'desc' ? 'descending' : header.column.getCanSort() ? 'none' : undefined} type="button" onClick={header.column.getToggleSortingHandler()} className="flex h-full min-w-0 items-center gap-1.5 px-3 text-left text-[11px] font-semibold text-ink-quiet outline-none transition-colors duration-standard hover:text-ink-secondary focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-signal-blue" style={{ flex: `${header.getSize()} 1 0` }}>
                  <span className="truncate">{header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}</span>
                  {header.column.getCanSort() ? sorted === 'asc' ? <ArrowUp className="size-3" /> : sorted === 'desc' ? <ArrowDown className="size-3" /> : <ChevronsUpDown className="size-3 opacity-45" /> : null}
                </button>
              );
            })}
          </div>
        ))}
      </div>
      {rows.length ? (
        <div ref={parentRef} role="rowgroup" className="overflow-y-auto" style={{ height }}>
          <div className="relative w-full" style={{ height: virtualizer.getTotalSize() }}>
            {virtualizer.getVirtualItems().map((virtualRow) => {
              const row = rows[virtualRow.index] as Row<T>;
              const selected = isRowSelected?.(row.original);
              return (
                <div key={row.id} role="row" aria-selected={selected} aria-rowindex={virtualRow.index + 1} aria-label={keyboardColumnLabel?.(row.original)} tabIndex={onRowClick ? (focusedRowIndex === virtualRow.index ? 0 : -1) : undefined} onFocus={() => setFocusedRowIndex(virtualRow.index)} onClick={() => { setFocusedRowIndex(virtualRow.index); onRowClick?.(row.original); }} onKeyDown={(event) => {
                  if (!onRowClick) return;
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    onRowClick(row.original);
                    return;
                  }
                  if (event.key === 'ArrowDown') {
                    event.preventDefault();
                    handleKeyboardSelection(Math.min(rows.length - 1, virtualRow.index + 1));
                    return;
                  }
                  if (event.key === 'ArrowUp') {
                    event.preventDefault();
                    handleKeyboardSelection(Math.max(0, virtualRow.index - 1));
                  }
                }} className={cn('absolute left-0 top-0 flex w-full items-center border-b border-line/75 text-xs text-ink-secondary transition-colors duration-standard hover:bg-graphite-hover/65 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-signal-blue', onRowClick && 'cursor-pointer', selected && 'bg-signal-blue/[0.08] text-ink', focusedRowIndex === virtualRow.index && 'ring-1 ring-inset ring-signal-blue/30')} style={{ height: rowHeight, transform: `translateY(${virtualRow.start}px)` }}>
                  {row.getVisibleCells().map((cell) => <div key={cell.id} role="cell" className="min-w-0 truncate px-3" style={{ flex: `${cell.column.getSize()} 1 0` }}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</div>)}
                </div>
              );
            })}
          </div>
        </div>
      ) : <div className="grid h-40 place-items-center text-xs text-ink-quiet">{emptyLabel}</div>}
    </div>
  );
}
