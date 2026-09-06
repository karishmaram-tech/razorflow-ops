# RecoveryFlow

Autonomous revenue recovery for failed payments — a public homepage plus a
Recovery Command Center where every failed payment is investigated, scored,
and worked by a seven-agent decision pipeline (Investigation → Prediction →
Economics → Risk → Strategy → Execution → Verification), with full autonomy
controls and an auditable trail of every action.

All payment, customer, and outcome data in this build is synthetically
generated on the client for demonstration — see `src/lib/engine.js`. No
production payment processor is connected.

## Routes

- `/` — public homepage (product explanation, live preview of real metrics, "Enter RecoveryFlow" CTA)
- `/app` — Command Center (the main authenticated-feeling product)
- `/app/payments/:id` — full agent reasoning trace for one payment
- `/app/strategies`, `/app/analytics`, `/app/control-center`, `/app/audit-log`
- `/app/sandbox` — generate synthetic events by scenario and run an accelerated batch through the real pipeline (this is where the old "run demo" button now lives — the Command Center itself runs continuously without it)

## Stack

- React 19 + Vite
- Tailwind CSS v4 (design tokens in `src/index.css`)
- react-router-dom for routing
- recharts for analytics charts
- lucide-react for icons

## Getting started

```bash
npm install
npm run dev       # local dev server
npm run build     # production build to dist/
npm run preview   # serve the production build locally
```

## Project structure

```
src/
  lib/
    domain.js            # failure reasons, strategies, agent roster
    engine.js             # the seven-agent decision pipeline (pure functions)
    RecoveryContext.jsx    # global state: payments, controls, audit log, ticking simulation
    format.js, stages.js, useCountUp.js
  components/
    ui/                   # Badge, Button, Card, Modal, StatCard, Toggle, Tooltip, EmptyState
    layout/                # Sidebar, MobileNav, Shell
    agents/                # PipelineTrack, StatusBadge, AgentTraceList
    dashboard/             # MetricsRow, AttentionTable, LiveActivityFeed, RecoverySimulation
  pages/
    RecoveryDashboard.jsx   # command center
    PaymentDetail.jsx        # full agent reasoning trace for one payment
    Strategies.jsx            # strategy performance comparison
    Analytics.jsx              # charts
    ControlCenter.jsx           # autonomy limits + pending approvals
    AuditLog.jsx                  # traceable action log + CSV export
```

## Notable behaviour

- **Run recovery simulation** (command center) fast-forwards 14 simulated
  failed payments through the full pipeline and reports a summary,
  including a "what RecoveryFlow learned" line comparing strategy
  performance in that run.
- **Agent disagreement**: the Risk Agent can override the default strategy
  when repeated contact attempts or a high-value payment raise
  customer-friction risk — visible as a callout in the payment detail
  trace and roughly 1-2 times per 14-payment simulation run.
- **Control Center**: autonomy thresholds (max retry attempts, intervention
  cost, confidence threshold, human-approval threshold, automatic
  execution toggle) actually gate which payments require manual approval.
- State lives in memory only (React context) and resets on a full page
  reload; there is no backend in this build.
