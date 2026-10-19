'use client';

import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Stethoscope } from 'lucide-react';
import Link from 'next/link';
import { Button, buttonVariants } from '@/components/ui/button';

interface SectionErrorBoundaryProps {
  children: ReactNode;
  title: string;
  detail: string;
  resetKey?: string | number;
  diagnosticsHref?: string;
}

interface SectionErrorBoundaryState {
  failed: boolean;
}

export class SectionErrorBoundary extends Component<SectionErrorBoundaryProps, SectionErrorBoundaryState> {
  state: SectionErrorBoundaryState = { failed: false };

  static getDerivedStateFromError(): SectionErrorBoundaryState {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[section-error-boundary]', this.props.title, error, info.componentStack);
  }

  componentDidUpdate(previous: SectionErrorBoundaryProps) {
    if (this.state.failed && previous.resetKey !== this.props.resetKey) {
      this.setState({ failed: false });
    }
  }

  private retry = () => this.setState({ failed: false });

  render() {
    if (!this.state.failed) return this.props.children;

    return (
      <section role="alert" className="rounded-md border border-failure/40 bg-failure/[0.06] p-5" data-section-error-boundary>
        <div className="flex items-start gap-3">
          <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-failure/10 text-failure" aria-hidden="true">
            <AlertTriangle className="size-4" />
          </span>
          <div className="min-w-0 flex-1">
            <h2 className="text-base font-semibold text-ink">{this.props.title}</h2>
            <p className="mt-1 max-w-2xl text-sm leading-6 text-ink-secondary">{this.props.detail}</p>
            <p className="mt-2 text-xs leading-5 text-ink-quiet">The rest of the console remains available.</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Button variant="primary" size="sm" onClick={this.retry}><RefreshCw className="size-4" />Retry section</Button>
              {this.props.diagnosticsHref ? <Link href={this.props.diagnosticsHref} className={buttonVariants({ variant: 'secondary', size: 'sm' })}><Stethoscope className="size-4" />Open diagnostics</Link> : null}
            </div>
          </div>
        </div>
      </section>
    );
  }
}

