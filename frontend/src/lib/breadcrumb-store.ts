import { useSyncExternalStore } from 'react';

let currentLabel: string | null = null;
const listeners = new Set<() => void>();

export const breadcrumbStore = {
  setLabel(label: string | null) {
    currentLabel = label;
    listeners.forEach((l) => l());
  },
  getLabel() {
    return currentLabel;
  },
  subscribe(listener: () => void) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
};

export function useBreadcrumbOverride() {
  return useSyncExternalStore(breadcrumbStore.subscribe, breadcrumbStore.getLabel, breadcrumbStore.getLabel);
}
