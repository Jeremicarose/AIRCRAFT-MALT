# Manual browser review — 19 October 2026

Scope: local historical replay production frontend at loopback ports 4328/4329.
Used agent-browser 0.27.0 with an isolated session and the historical fixture.
Checked source labels, 362/270/92 counts, original relative arrival times, solved
and rejected detail views, component diagnostics and the export action. No wallet
was connected, no form sent, no real feed configured. The browser error command
returned no application errors.

The native automation click on an offscreen event link reported success without
changing the URL. A direct load showed the correct rejection. A new permanent
Playwright test actually clicked the event link and both pagination links; all
three historical browser tests passed. This is recorded as an automation
limitation, not a confirmed application navigation defect. Earlier screenshots
named replay-rejected still showed event 14040; they are retained locally and
are not evidence of a successful rejected-event navigation. The final
historical-rejection-confirmed.png captures the direct rejected-event view.

Browser services and isolated browser session were stopped after review.
No new visual defect was confirmed in this limited walkthrough. It is not a
comprehensive visual audit or an independent accessibility certification.
