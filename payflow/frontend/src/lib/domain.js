// Domain constants for RecoveryFlow.
// All data in this app is simulated for demonstration — see lib/engine.js.

export const FAILURE_REASONS = {
  BANK_DECLINED: {
    label: 'Bank declined',
    description: 'The issuing bank returned a soft decline with no fraud signal — often a temporary hold or risk-rule bounce.',
    baseRecovery: 0.82,
    bestStrategy: 'delayed_retry',
  },
  NETWORK_ERROR: {
    label: 'Network error',
    description: 'The authorization request failed in transit between processor and issuer. No customer-side issue.',
    baseRecovery: 0.91,
    bestStrategy: 'immediate_retry',
  },
  INSUFFICIENT_FUNDS: {
    label: 'Insufficient funds',
    description: 'The account did not have sufficient balance at the time of the charge.',
    baseRecovery: 0.46,
    bestStrategy: 'delayed_retry',
  },
  EXPIRED_CARD: {
    label: 'Expired card',
    description: 'The card on file has passed its expiry date. Retrying the same instrument will not succeed.',
    baseRecovery: 0.21,
    bestStrategy: 'method_fallback',
  },
  LIMIT_EXCEEDED: {
    label: 'Limit exceeded',
    description: 'The transaction exceeded a per-transaction or daily limit set by the issuer.',
    baseRecovery: 0.58,
    bestStrategy: 'delayed_retry',
  },
  AUTHENTICATION_FAILED: {
    label: 'Authentication failed',
    description: 'The 3-D Secure / OTP step was not completed or timed out.',
    baseRecovery: 0.63,
    bestStrategy: 'customer_notification',
  },
  PROCESSOR_TIMEOUT: {
    label: 'Processor timeout',
    description: 'The payment processor did not respond within the authorization window.',
    baseRecovery: 0.88,
    bestStrategy: 'immediate_retry',
  },
};

export const STRATEGIES = {
  immediate_retry: {
    label: 'Immediate retry',
    description: 'Re-attempt the same charge on the same instrument within minutes.',
    cost: 6,
    friction: 'Low',
  },
  delayed_retry: {
    label: 'Delayed retry',
    description: 'Wait for a favourable window (payday, balance refresh) before re-attempting.',
    cost: 6,
    friction: 'Low',
  },
  method_fallback: {
    label: 'Payment-method fallback',
    description: 'Charge a backup instrument on file instead of the failed one.',
    cost: 14,
    friction: 'Low',
  },
  customer_notification: {
    label: 'Customer notification',
    description: 'Prompt the customer to update or re-authenticate their payment method.',
    cost: 22,
    friction: 'Medium',
  },
  escalation: {
    label: 'Escalation',
    description: 'Route to a human recovery specialist for high-value or sensitive accounts.',
    cost: 180,
    friction: 'Medium',
  },
  invoice_recovery: {
    label: 'Invoice recovery',
    description: 'Convert to a standing invoice with extended payment terms.',
    cost: 40,
    friction: 'Medium',
  },
  human_review: {
    label: 'Human review',
    description: 'Hold for manual approval before any customer-facing action is taken.',
    cost: 0,
    friction: 'None (pending)',
  },
};

export const PAYMENT_METHODS = ['UPI', 'Credit card', 'Debit card', 'Net banking', 'Wallet'];

export const PROCESSORS = ['Razorpay (simulated)', 'Cashfree (simulated)', 'PayU (simulated)'];

export const AGENTS = [
  {
    key: 'investigation',
    name: 'Investigation Agent',
    role: 'Classifies the failure using processor codes, issuer response, and attempt history.',
    stage: 'Investigating',
  },
  {
    key: 'prediction',
    name: 'Prediction Agent',
    role: 'Scores the probability of recovery from historical outcomes on comparable payments.',
    stage: 'Predicting',
  },
  {
    key: 'economics',
    name: 'Economics Agent',
    role: 'Weighs expected recovered value against the cost of each available action.',
    stage: 'Evaluating',
  },
  {
    key: 'risk',
    name: 'Risk Agent',
    role: 'Flags customer-friction and compliance risk in the proposed action.',
    stage: 'Evaluating',
  },
  {
    key: 'strategy',
    name: 'Strategy Agent',
    role: 'Selects the action with the best risk-adjusted expected value.',
    stage: 'Deciding',
  },
  {
    key: 'execution',
    name: 'Execution Agent',
    role: 'Carries out the selected action against the processor or notification service.',
    stage: 'Executing',
  },
  {
    key: 'verification',
    name: 'Verification Agent',
    role: 'Confirms the outcome and feeds it back into the prediction model.',
    stage: 'Verifying',
  },
];

export const STAGE_SEQUENCE = [
  'queued',
  'investigating',
  'predicting',
  'evaluating',
  'deciding',
  'awaiting_approval',
  'executing',
  'verifying',
  'resolved',
];

export const STAGE_LABELS = {
  queued: 'Queued',
  investigating: 'Investigating',
  predicting: 'Predicting',
  evaluating: 'Evaluating',
  deciding: 'Deciding',
  awaiting_approval: 'Awaiting approval',
  executing: 'Executing',
  verifying: 'Verifying',
  resolved: 'Resolved',
};
