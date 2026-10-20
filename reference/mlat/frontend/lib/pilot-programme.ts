export type PilotApplicationStatus = 'preparing' | 'interest' | 'open' | 'closed';
export type PilotFundingStatus = 'seeking' | 'funded';

export interface PilotProgrammeConfig {
  applicationStatus?: string;
  fundingStatus?: string;
  applicationUrl?: string;
}

export interface PilotProgrammeState {
  applicationStatus: PilotApplicationStatus;
  fundingStatus: PilotFundingStatus;
  applicationUrl: string | null;
  applicationsOpen: boolean;
  interestOpen: boolean;
}

export function resolvePilotProgramme(config: PilotProgrammeConfig): PilotProgrammeState {
  const applicationStatus = normalizeApplicationStatus(config.applicationStatus);
  const fundingStatus = config.fundingStatus === 'funded' ? 'funded' : 'seeking';
  const applicationUrl = safePublicUrl(config.applicationUrl);

  return {
    applicationStatus,
    fundingStatus,
    applicationUrl,
    applicationsOpen: applicationStatus === 'open' && fundingStatus === 'funded' && applicationUrl !== null,
    interestOpen: applicationStatus === 'interest' && applicationUrl !== null,
  };
}

function normalizeApplicationStatus(value: string | undefined): PilotApplicationStatus {
  return value === 'interest' || value === 'open' || value === 'closed' ? value : 'preparing';
}

function safePublicUrl(value: string | undefined): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    return url.protocol === 'https:' ? url.toString() : null;
  } catch {
    return null;
  }
}
