import type { ShellSnapshot, StatusTone } from '@/lib/types';

export type OperatorNoticeSeverity = 'error' | 'warning';

export interface OperatorNotice {
  id: string;
  title: string;
  detail: string;
  severity: OperatorNoticeSeverity;
  tone: StatusTone;
  href: string;
  focus: string;
}

export function operatorNotices(snapshot: ShellSnapshot): OperatorNotice[] {
  const notices: OperatorNotice[] = [];
  const mode = snapshot.modeData;

  if (!mode) {
    notices.push({
      id: 'runtime',
      title: 'Runtime unavailable',
      detail: 'The environment endpoint did not respond. Open Diagnostics to check the API connection.',
      severity: 'error',
      tone: 'failure',
      href: '/app/environment',
      focus: 'runtime',
    });
  } else if (!mode.receiver_registry_type_hash) {
    notices.push({
      id: 'registry',
      title: 'Registry configuration missing',
      detail: 'The runtime cannot verify or discover Registry identities until its Registry code hash is configured.',
      severity: 'warning',
      tone: 'attention',
      href: '/app/environment',
      focus: 'registry',
    });
  }

  if (snapshot.receiverData) {
    const receiverCount = snapshot.receiverData.count ?? snapshot.receiverData.receivers?.length ?? 0;
    if (receiverCount < 4) {
      notices.push({
        id: 'receivers',
        title: 'Receiver geometry insufficient',
        detail: `${receiverCount} operational receivers are available; an MLAT solve requires at least four qualified receivers.`,
        severity: 'error',
        tone: 'failure',
        href: '/app/pipeline',
        focus: 'geometry',
      });
    }
  }

  return [...new Map(notices.map((notice) => [notice.id, notice])).values()];
}
