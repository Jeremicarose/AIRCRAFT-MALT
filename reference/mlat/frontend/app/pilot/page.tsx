import type { Metadata } from 'next';
import Image from 'next/image';
import Link from 'next/link';
import {
  ArrowRight,
  Check,
  CircleDollarSign,
  Clock3,
  ExternalLink,
  RadioTower,
  ShieldCheck,
  Users,
} from 'lucide-react';
import workflowDiagram from '../../../../../docs/pilot/assets/receiver-workflow.png';
import boundaryDiagram from '../../../../../docs/pilot/assets/registry-mlat-boundary.png';
import { buttonVariants } from '@/components/ui/button';
import { resolvePilotProgramme } from '@/lib/pilot-programme';
import { cn } from '@/lib/utils';

export const metadata: Metadata = {
  title: 'Operator Pilot',
  description: 'Apply to test stable CKB identities and lifecycle evidence for independently operated ADS-B and Mode S receivers.',
};

const {
  applicationStatus,
  fundingStatus,
  applicationUrl,
  applicationsOpen,
  interestOpen,
} = resolvePilotProgramme({
  applicationStatus: process.env.NEXT_PUBLIC_PILOT_APPLICATION_STATUS,
  fundingStatus: process.env.NEXT_PUBLIC_PILOT_FUNDING_STATUS,
  applicationUrl: process.env.NEXT_PUBLIC_PILOT_APPLICATION_URL,
});

const status = applicationsOpen
  ? {
      label: 'Applications open',
      detail: 'Participant incentives are funded and eligible operators may apply.',
      tone: 'text-healthy border-healthy/35 bg-healthy/[0.08]',
    }
  : interestOpen
    ? {
        label: 'Interest list open',
        detail: fundingStatus === 'funded'
          ? 'Funding is confirmed. Sessions will be scheduled after the readiness gate passes.'
          : 'Funding is being sought. Joining the list does not guarantee selection or payment.',
        tone: 'text-attention border-attention/35 bg-attention/[0.08]',
      }
    : applicationStatus === 'closed'
      ? {
          label: 'Applications closed',
          detail: 'The current cohort is no longer accepting applications.',
          tone: 'text-ink-secondary border-line bg-graphite-raised',
        }
      : {
          label: 'Programme preparation',
          detail: fundingStatus === 'funded'
            ? 'Participant funding is confirmed. The application and session environment are being prepared.'
            : 'The pilot package is ready, but participant funding and the final readiness checks are not complete.',
          tone: 'text-attention border-attention/35 bg-attention/[0.08]',
        };

const participantTracks = [
  {
    count: 4,
    title: 'Receiver owners and operators',
    eligibility: 'Operating an ADS-B or Mode S receiver now, or within the last 12 months.',
    tasks: ['Create and update a test receiver identity', 'Inspect ownership and lifecycle history', 'Return within seven days and find it again'],
    commitment: '85-95 minutes total',
    wallet: 'A supported CKB Pudge testnet wallet is required for owner actions.',
  },
  {
    count: 2,
    title: 'Network coordinators and developers',
    eligibility: 'Responsible for multiple receiver records, feeds, monitoring, or integrations.',
    tasks: ['Discover and interpret assigned identities', 'Export documented JSON', 'Review one realistic integration path'],
    commitment: '90-120 minutes total',
    wallet: 'No wallet is required for directory, evidence, and export tasks.',
  },
];

function ApplicationAction() {
  if (applicationsOpen || interestOpen) {
    return (
      <a
        href={applicationUrl ?? undefined}
        target="_blank"
        rel="noreferrer"
        className={buttonVariants({ variant: 'primary', size: 'default' })}
      >
        {applicationsOpen ? 'Apply for the pilot' : 'Join the interest list'}
        <ExternalLink className="size-4" aria-hidden="true" />
      </a>
    );
  }

  return (
    <span className="inline-flex h-9 items-center rounded-md border border-line bg-graphite-raised px-3 text-[13px] font-semibold text-ink-quiet" aria-disabled="true">
      Applications are not open
    </span>
  );
}

export default function PilotPage() {
  return (
    <main className="min-h-screen bg-graphite-deep text-ink">
      <a href="#pilot-content" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[80] focus:rounded-md focus:bg-signal-blue focus:px-3 focus:py-2 focus:font-semibold focus:text-graphite-deep">
        Skip to pilot details
      </a>

      <header className="border-b border-line bg-graphite-deep/95">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-5 sm:px-8">
          <Link href="/app/registry" className="flex min-w-0 items-center gap-3 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-blue">
            <span className="grid size-9 shrink-0 place-items-center rounded-md border border-trust-cyan/40 bg-trust-cyan/10 font-mono text-sm font-semibold text-trust-cyan">R</span>
            <span className="min-w-0">
              <span className="block truncate text-sm font-semibold">CKB Receiver Registry</span>
              <span className="block text-xs text-ink-quiet">Operator pilot</span>
            </span>
          </Link>
          <Link href="/app/registry" className={buttonVariants({ variant: 'secondary', size: 'sm' })}>
            Open Registry
            <ArrowRight className="size-3.5" aria-hidden="true" />
          </Link>
        </div>
      </header>

      <section className="relative isolate overflow-hidden border-b border-line">
        <Image
          src={workflowDiagram}
          alt=""
          fill
          priority
          sizes="100vw"
          className="-z-20 object-cover object-center opacity-[0.16]"
        />
        <div className="absolute inset-0 -z-10 bg-graphite-deep/80" />
        <div className="mx-auto flex min-h-[620px] max-w-7xl flex-col justify-center px-5 py-16 sm:px-8 lg:py-20">
          <div className="max-w-3xl">
            <div className={cn('mb-7 inline-flex max-w-full items-start gap-3 rounded-md border px-3 py-2 text-sm', status.tone)} role="status">
              <span className="mt-1 size-2 shrink-0 rounded-full bg-current" aria-hidden="true" />
              <span><strong className="font-semibold">{status.label}.</strong> <span className="text-ink-secondary">{status.detail}</span></span>
            </div>
            <h1 className="max-w-2xl text-4xl font-semibold leading-[1.08] text-wrap-balance sm:text-5xl lg:text-6xl">
              CKB Receiver Registry Pilot
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-ink-secondary text-wrap-pretty sm:text-xl">
              Help test whether one owner-controlled receiver identity can remain useful as metadata, status, network, and ownership change.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <ApplicationAction />
              <a
                href="https://github.com/Jeremicarose/AIRCRAFT-MALT"
                target="_blank"
                rel="noreferrer"
                className={buttonVariants({ variant: 'ghost', size: 'default' })}
              >
                Review source
                <ExternalLink className="size-4" aria-hidden="true" />
              </a>
            </div>
            <dl className="mt-12 grid max-w-3xl grid-cols-1 border-y border-line sm:grid-cols-3">
              <div className="py-4 sm:pr-5">
                <dt className="text-xs font-medium text-ink-quiet">Cohort</dt>
                <dd className="mt-1 text-base font-semibold">6 participants</dd>
              </div>
              <div className="border-line py-4 sm:border-x sm:px-5">
                <dt className="text-xs font-medium text-ink-quiet">Format</dt>
                <dd className="mt-1 text-base font-semibold">Remote, moderated</dd>
              </div>
              <div className="py-4 sm:pl-5">
                <dt className="text-xs font-medium text-ink-quiet">Environment</dt>
                <dd className="mt-1 text-base font-semibold">CKB Pudge testnet</dd>
              </div>
            </dl>
          </div>
        </div>
      </section>

      <div id="pilot-content">
        <section className="border-b border-line py-16 sm:py-20">
          <div className="mx-auto max-w-7xl px-5 sm:px-8">
            <div className="max-w-3xl">
              <h2 className="text-3xl font-semibold text-wrap-balance">Two operating roles, one shared question</h2>
              <p className="mt-4 max-w-2xl text-base leading-7 text-ink-secondary">
                We need people with practical receiver experience. Blockchain experience is not required, and physical receiver hardware is not connected during the study.
              </p>
            </div>
            <div className="mt-10 grid gap-5 lg:grid-cols-2">
              {participantTracks.map((track) => (
                <article key={track.title} className="rounded-lg border border-line bg-graphite p-6 sm:p-8">
                  <div className="flex items-start gap-5">
                    <span className="grid size-14 shrink-0 place-items-center rounded-full bg-trust-cyan text-2xl font-semibold text-graphite-deep">{track.count}</span>
                    <div>
                      <h3 className="text-xl font-semibold">{track.title}</h3>
                      <p className="mt-2 text-sm leading-6 text-ink-secondary">{track.eligibility}</p>
                    </div>
                  </div>
                  <ul className="mt-7 space-y-3">
                    {track.tasks.map((task) => (
                      <li key={task} className="flex gap-3 text-sm leading-6 text-ink-secondary">
                        <Check className="mt-1 size-4 shrink-0 text-healthy" aria-hidden="true" />
                        <span>{task}</span>
                      </li>
                    ))}
                  </ul>
                  <div className="mt-7 border-t border-line pt-5 text-sm">
                    <p className="flex items-center gap-2 font-semibold"><Clock3 className="size-4 text-signal-blue" aria-hidden="true" />{track.commitment}</p>
                    <p className="mt-2 leading-6 text-ink-quiet">{track.wallet}</p>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="border-b border-line bg-graphite py-16 sm:py-20">
          <div className="mx-auto grid max-w-7xl items-start gap-10 px-5 sm:px-8 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
            <div className="max-w-xl">
              <h2 className="text-3xl font-semibold text-wrap-balance">What the study is actually testing</h2>
              <p className="mt-4 text-base leading-7 text-ink-secondary">
                Registry lifecycle evidence and MLAT operation are related, but they are not the same proof. The session tests whether that boundary is useful and understandable in real receiver workflows.
              </p>
              <ul className="mt-8 space-y-5">
                <li className="flex gap-4">
                  <ShieldCheck className="mt-0.5 size-5 shrink-0 text-trust-cyan" aria-hidden="true" />
                  <div><strong className="font-semibold">Registry evidence</strong><p className="mt-1 text-sm leading-6 text-ink-secondary">Stable identity, current owner authorization, ordered changes, and permanent revocation.</p></div>
                </li>
                <li className="flex gap-4">
                  <RadioTower className="mt-0.5 size-5 shrink-0 text-signal-blue" aria-hidden="true" />
                  <div><strong className="font-semibold">Operational qualification</strong><p className="mt-1 text-sm leading-6 text-ink-secondary">Feed binding, timing, freshness, geometry, observations, and contribution remain separate checks.</p></div>
                </li>
              </ul>
            </div>
            <figure className="overflow-hidden rounded-lg border border-line bg-graphite-deep">
              <Image src={boundaryDiagram} alt="Registry V2 verifies receiver identity, ownership, lifecycle, and discovery. MLAT separately uses qualified observations to estimate aircraft positions." sizes="(min-width: 1024px) 58vw, 100vw" className="h-auto w-full" />
              <figcaption className="border-t border-line px-4 py-3 text-xs leading-5 text-ink-quiet">Responsibility boundary used throughout the pilot.</figcaption>
            </figure>
          </div>
        </section>

        <section className="border-b border-line py-16 sm:py-20">
          <div className="mx-auto grid max-w-7xl gap-12 px-5 sm:px-8 lg:grid-cols-2">
            <div>
              <h2 className="text-3xl font-semibold">Privacy and safety</h2>
              <p className="mt-4 max-w-xl text-base leading-7 text-ink-secondary">The study does not need access to your physical receiver or private feed.</p>
              <ul className="mt-7 space-y-3 text-sm leading-6 text-ink-secondary">
                {[
                  'Never share a private key, seed phrase, password, feed credential, or IP address.',
                  'Use fictional or deliberately coarse coordinates in test records.',
                  'Every testnet transaction is reviewed and approved in your own wallet.',
                  'The application is experimental and must not be used for aviation safety decisions.',
                ].map((item) => <li key={item} className="flex gap-3"><Check className="mt-1 size-4 shrink-0 text-healthy" aria-hidden="true" /><span>{item}</span></li>)}
              </ul>
            </div>
            <div>
              <h2 className="text-3xl font-semibold">Participant payment</h2>
              <div className="mt-5 flex gap-4 rounded-lg border border-line bg-graphite p-5">
                <CircleDollarSign className="size-6 shrink-0 text-attention" aria-hidden="true" />
                <div>
                  <p className="font-semibold">{fundingStatus === 'funded' ? 'Funded completion incentive' : 'Proposed completion incentive'}</p>
                  <p className="mt-2 text-sm leading-6 text-ink-secondary">
                    The programme proposes a $30 USD-equivalent payment after the session, interview, and agreed follow-up are complete.
                    {fundingStatus === 'funded' ? ' Funding is confirmed for the current cohort.' : ' Funding is not confirmed yet, so this is not a promise of payment.'}
                  </p>
                </div>
              </div>
              <p className="mt-5 flex items-start gap-3 text-sm leading-6 text-ink-secondary">
                <Users className="mt-1 size-4 shrink-0 text-signal-blue" aria-hidden="true" />
                Selection is based on role fit, practical experience, cohort balance, availability, and technical readiness. Applying does not guarantee a place.
              </p>
            </div>
          </div>
        </section>

        <section className="py-16 sm:py-20">
          <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-8 px-5 sm:px-8 lg:flex-row lg:items-center">
            <div className="max-w-2xl">
              <h2 className="text-3xl font-semibold text-wrap-balance">Help decide whether this product direction should continue</h2>
              <p className="mt-4 text-base leading-7 text-ink-secondary">Positive feedback is not required. A clear rejection, operational objection, or integration blocker is useful evidence.</p>
            </div>
            <div className="flex shrink-0 flex-wrap gap-3">
              <ApplicationAction />
              <Link href="/app/registry" className={buttonVariants({ variant: 'secondary', size: 'default' })}>Explore the Registry<ArrowRight className="size-4" aria-hidden="true" /></Link>
            </div>
          </div>
        </section>
      </div>

      <footer className="border-t border-line bg-graphite py-8">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-5 text-xs leading-5 text-ink-quiet sm:px-8 lg:flex-row lg:items-center lg:justify-between">
          <p>CKB Pudge testnet. Experimental and unaudited. Not for aviation safety decisions.</p>
          <p>Registry records are public. Never publish precise private receiver locations.</p>
        </div>
      </footer>
    </main>
  );
}
