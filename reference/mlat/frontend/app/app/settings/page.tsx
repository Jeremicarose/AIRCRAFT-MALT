import { AppShell } from '@/components/app-shell';
import { SettingsPage } from '@/components/pages/settings-page';
import { fetchShellSnapshot } from '@/lib/api';

export default async function SettingsRoute() {
  const snapshot = await fetchShellSnapshot();
  return <AppShell pageKey="settings" title="Settings" description="Configure local console behavior and display defaults." snapshot={snapshot}><SettingsPage /></AppShell>;
}
