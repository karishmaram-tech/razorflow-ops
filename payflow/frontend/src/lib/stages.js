export const DISPLAY_STEPS = [
  { key: 'investigating', label: 'Investigate' },
  { key: 'predicting', label: 'Predict' },
  { key: 'evaluating', label: 'Evaluate' },
  { key: 'executing', label: 'Execute' },
  { key: 'verifying', label: 'Verify' },
  { key: 'resolved', label: 'Resolved' },
];

const ORDER = ['queued', 'investigating', 'predicting', 'evaluating', 'awaiting_approval', 'executing', 'verifying', 'resolved'];

// Returns the index into DISPLAY_STEPS representing progress so far.
// awaiting_approval freezes progress at "evaluating complete".
export function stepIndex(stage) {
  const raw = ORDER.indexOf(stage);
  if (stage === 'awaiting_approval') return DISPLAY_STEPS.findIndex((s) => s.key === 'evaluating');
  const map = {
    queued: -1,
    investigating: 0,
    predicting: 1,
    evaluating: 2,
    executing: 3,
    verifying: 4,
    resolved: 5,
  };
  return map[stage] ?? raw;
}

export function stageStatusLabel(payment) {
  if (payment.stage === 'awaiting_approval') return 'Awaiting approval';
  if (payment.stage === 'resolved') {
    if (payment.outcome?.rejected) return 'Rejected';
    return payment.outcome?.recovered ? 'Recovered' : 'Not recovered';
  }
  const found = DISPLAY_STEPS.find((s) => s.key === payment.stage);
  return found ? found.label : 'Queued';
}
