'use client';

import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { validCompletions, type MissionId } from './missions.ts';

interface MissionState {
  hydrated: boolean;
  enabled: boolean;
  completed: MissionId[];
  latest: MissionId | null;
  complete: (id: MissionId) => void;
  dismiss: () => void;
  reset: () => void;
  setEnabled: (value: boolean) => void;
  setHydrated: () => void;
}

// Storage is optional. No receiver identity, wallet address or API data is stored.
const storage = createJSONStorage(() => ({
  getItem: (key: string) => { try { return window.localStorage.getItem(key); } catch { return null; } },
  setItem: (key: string, value: string) => { try { window.localStorage.setItem(key, value); } catch { /* Continue in memory. */ } },
  removeItem: (key: string) => { try { window.localStorage.removeItem(key); } catch { /* Continue in memory. */ } },
}));

export const useMissionStore = create<MissionState>()(persist((set) => ({
  hydrated: false,
  enabled: true,
  completed: [],
  latest: null,
  complete: (id) => set((state) => {
    if (!state.hydrated || !state.enabled || state.completed.includes(id) || !validCompletions([id]).length) return state;
    return { completed: validCompletions([...state.completed, id]), latest: id };
  }),
  dismiss: () => set({ latest: null }),
  reset: () => set({ completed: [], latest: null }),
  setEnabled: (enabled) => set({ enabled, latest: null }),
  setHydrated: () => set({ hydrated: true }),
}), {
  name: 'receiver-console-missions-v1',
  version: 1,
  storage,
  skipHydration: true,
  partialize: ({ completed, enabled }) => ({ completed, enabled }),
  merge: (persisted, current) => {
    const saved = persisted && typeof persisted === 'object' ? persisted as Record<string, unknown> : {};
    return { ...current, completed: validCompletions(saved.completed), enabled: saved.enabled !== false };
  },
}));
