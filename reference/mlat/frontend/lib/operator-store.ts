'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { InvestigationDockState, StatusTone } from '@/lib/types';

interface InvestigationState {
  routeKey?: string;
  query?: string;
  focus?: string;
  timeRange?: string;
  watchlist?: string[];
}

export interface RouteHistoryEntry {
  key: string;
  label: string;
  href: string;
  visitedAt: number;
}

export interface RecentInvestigationEntry {
  id: string;
  title: string;
  entityType: InvestigationDockState['entityType'];
  routeKey?: string;
  href?: string;
  focus?: string;
  statusLabel?: string;
  statusTone?: StatusTone;
  updatedAt: number;
}

interface OperatorState {
  sidebarCollapsed: boolean;
  mobileNavigationOpen: boolean;
  commandOpen: boolean;
  rightDockOpen: boolean;
  density: 'comfortable' | 'compact';
  selectedAircraftId: string | null;
  selectedReceiverId: string | null;
  showReceiverLinks: boolean;
  showUncertainty: boolean;
  investigation: InvestigationState;
  dock: InvestigationDockState | null;
  routeHistory: RouteHistoryEntry[];
  starredRoutes: string[];
  recentInvestigations: RecentInvestigationEntry[];
  setSidebarCollapsed: (value: boolean) => void;
  setMobileNavigationOpen: (value: boolean) => void;
  setCommandOpen: (value: boolean) => void;
  setRightDockOpen: (value: boolean) => void;
  setDensity: (value: 'comfortable' | 'compact') => void;
  setSelectedAircraftId: (value: string | null) => void;
  setSelectedReceiverId: (value: string | null) => void;
  toggleReceiverLinks: () => void;
  toggleUncertainty: () => void;
  setInvestigationContext: (value: Partial<InvestigationState>) => void;
  clearInvestigationContext: () => void;
  setDock: (value: InvestigationDockState | null) => void;
  clearDock: () => void;
  pushRouteHistory: (entry: Omit<RouteHistoryEntry, 'visitedAt'>) => void;
  toggleStarredRoute: (routeKey: string) => void;
  pushRecentInvestigation: (entry: Omit<RecentInvestigationEntry, 'updatedAt'>) => void;
  clearRecentInvestigations: () => void;
}

const defaultInvestigationState: InvestigationState = {
  routeKey: undefined,
  query: '',
  focus: undefined,
  timeRange: '10m',
  watchlist: [],
};

export const useOperatorStore = create<OperatorState>()(persist((set) => ({
  sidebarCollapsed: false,
  mobileNavigationOpen: false,
  commandOpen: false,
  rightDockOpen: true,
  density: 'comfortable',
  selectedAircraftId: null,
  selectedReceiverId: null,
  showReceiverLinks: true,
  showUncertainty: true,
  investigation: defaultInvestigationState,
  dock: null,
  routeHistory: [],
  starredRoutes: ['overview', 'localization', 'aircraft'],
  recentInvestigations: [],
  setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
  setMobileNavigationOpen: (mobileNavigationOpen) => set({ mobileNavigationOpen }),
  setCommandOpen: (commandOpen) => set({ commandOpen }),
  setRightDockOpen: (rightDockOpen) => set({ rightDockOpen }),
  setDensity: (density) => set({ density }),
  setSelectedAircraftId: (selectedAircraftId) => set((state) => ({
    selectedAircraftId,
    investigation: {
      ...state.investigation,
      focus: selectedAircraftId ?? state.investigation.focus,
    },
  })),
  setSelectedReceiverId: (selectedReceiverId) => set((state) => ({
    selectedReceiverId,
    investigation: {
      ...state.investigation,
      focus: selectedReceiverId ?? state.investigation.focus,
    },
  })),
  toggleReceiverLinks: () => set((state) => ({ showReceiverLinks: !state.showReceiverLinks })),
  toggleUncertainty: () => set((state) => ({ showUncertainty: !state.showUncertainty })),
  setInvestigationContext: (value) => set((state) => ({ investigation: { ...state.investigation, ...value } })),
  clearInvestigationContext: () => set({ investigation: defaultInvestigationState }),
  setDock: (dock) => set({ dock }),
  clearDock: () => set({ dock: null }),
  pushRouteHistory: (entry) => set((state) => {
    const next = [{ ...entry, visitedAt: Date.now() }, ...state.routeHistory.filter((item) => item.key !== entry.key)];
    return { routeHistory: next.slice(0, 8) };
  }),
  toggleStarredRoute: (routeKey) => set((state) => ({
    starredRoutes: state.starredRoutes.includes(routeKey)
      ? state.starredRoutes.filter((item) => item !== routeKey)
      : [...state.starredRoutes, routeKey].slice(-6),
  })),
  pushRecentInvestigation: (entry) => set((state) => {
    const next = [{ ...entry, updatedAt: Date.now() }, ...state.recentInvestigations.filter((item) => item.id !== entry.id)];
    return { recentInvestigations: next.slice(0, 8) };
  }),
  clearRecentInvestigations: () => set({ recentInvestigations: [] }),
}), {
  name: 'mlat-console-operator-state',
  partialize: (state) => ({
    sidebarCollapsed: state.sidebarCollapsed,
    rightDockOpen: state.rightDockOpen,
    density: state.density,
    selectedAircraftId: state.selectedAircraftId,
    selectedReceiverId: state.selectedReceiverId,
    showReceiverLinks: state.showReceiverLinks,
    showUncertainty: state.showUncertainty,
    investigation: state.investigation,
    routeHistory: state.routeHistory,
    starredRoutes: state.starredRoutes,
    recentInvestigations: state.recentInvestigations,
  }),
}));
