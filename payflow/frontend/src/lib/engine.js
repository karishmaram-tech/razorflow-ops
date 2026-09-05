import { FAILURE_REASONS, STRATEGIES, PAYMENT_METHODS, PROCESSORS } from './domain';

// ---------------------------------------------------------------------------
// RecoveryFlow simulation engine.
// All payments, customers, and outcomes below are synthetically generated
// for demonstration. Nothing here touches a real processor or real customer
// data — see the "Simulated" badge shown throughout the product.
// ---------------------------------------------------------------------------

let idCounter = 3184;

const AMOUNT_POOL = [
  4999, 8750, 12499, 19999, 24900, 42300, 6499, 15999, 2999, 34500, 9999, 59900,
];

function weightedReason() {
  const weights = [
    ['BANK_DECLINED', 26],
    ['INSUFFICIENT_FUNDS', 22],
    ['NETWORK_ERROR', 10],
    ['EXPIRED_CARD', 14],
    ['LIMIT_EXCEEDED', 10],
    ['AUTHENTICATION_FAILED', 12],
    ['PROCESSOR_TIMEOUT', 6],
  ];
  const total = weights.reduce((s, [, w]) => s + w, 0);
  let r = Math.random() * total;
  for (const [key, w] of weights) {
    if (r < w) return key;
    r -= w;
  }
  return weights[0][0];
}

function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function jitter(base, spread = 0.12) {
  return base + (Math.random() * 2 - 1) * spread;
}

export function createPayment(now = new Date()) {
  const id = `RF-${idCounter++}`;
  const failureReason = weightedReason();
  const amount = pick(AMOUNT_POOL) + Math.round((Math.random() * 400) - 200);
  const attempts = Math.random() < 0.7 ? 1 : Math.random() < 0.85 ? 2 : 3;
  const customerTenureMonths = 1 + Math.floor(Math.random() * 30);

  return {
    id,
    amount: Math.max(999, amount),
    method: pick(PAYMENT_METHODS),
    processor: pick(PROCESSORS),
    failureReason,
    attempts,
    customerRef: `Customer •••${1000 + Math.floor(Math.random() * 8999)}`,
    customerTenureMonths,
    subscriptionPlan: amount > 30000 ? 'Annual plan' : 'Monthly plan',
    createdAt: now,
    stage: 'queued',
    trace: [],
    decision: null,
    outcome: null,
    stageEnteredAt: now,
  };
}

// --- Individual agent evaluations -----------------------------------------

export function runInvestigation(payment) {
  const info = FAILURE_REASONS[payment.failureReason];
  const evidence = [
    `Processor code: ${payment.failureReason}`,
    `${payment.attempts} prior attempt${payment.attempts > 1 ? 's' : ''} on this billing cycle`,
    `Instrument: ${payment.method} via ${payment.processor}`,
  ];
  return {
    agent: 'investigation',
    title: 'Investigation',
    finding: info.description,
    confidence: Math.round(jitter(0.94, 0.04) * 100),
    evidence,
  };
}

export function runPrediction(payment) {
  const info = FAILURE_REASONS[payment.failureReason];
  let probability = info.baseRecovery;
  if (payment.attempts >= 3) probability -= 0.18;
  if (payment.customerTenureMonths > 12) probability += 0.05;
  probability = Math.min(0.97, Math.max(0.04, jitter(probability, 0.06)));
  return {
    agent: 'prediction',
    title: 'Prediction',
    finding: `Recovery probability estimated at ${Math.round(probability * 100)}% based on ${312 + Math.floor(Math.random() * 900)} comparable payments in the last 90 days.`,
    confidence: Math.round(jitter(0.88, 0.06) * 100),
    probability,
    evidence: [
      `Cohort: ${info.label.toLowerCase()}, ${payment.method}`,
      `Customer tenure: ${payment.customerTenureMonths} months`,
      `Attempt number: ${payment.attempts}`,
    ],
  };
}

export function runEconomics(payment, prediction, candidateStrategyKey) {
  const strategy = STRATEGIES[candidateStrategyKey];
  const grossExpected = payment.amount * prediction.probability;
  const expectedNet = Math.round(grossExpected - strategy.cost);
  return {
    agent: 'economics',
    title: 'Economics',
    finding: `Expected net value of ${strategy.label.toLowerCase()} is ${expectedNet >= 0 ? 'positive' : 'negative'} after action cost.`,
    confidence: Math.round(jitter(0.9, 0.05) * 100),
    expectedNet,
    cost: strategy.cost,
    evidence: [
      `Gross expected recovery: ${Math.round(grossExpected)}`,
      `Action cost: ₹${strategy.cost}`,
      `Net expected value: ${expectedNet >= 0 ? '+' : ''}${expectedNet}`,
    ],
  };
}

export function runRisk(payment, prediction, candidateStrategyKey) {
  const strategy = STRATEGIES[candidateStrategyKey];
  // Friction is a function of how much this customer has already been
  // bothered, not just the inherent friction class of the candidate action —
  // repeated contact is what erodes goodwill, regardless of which low-touch
  // action is proposed next.
  let frictionScore = 0.12 + payment.attempts * 0.16;
  if (payment.amount > 40000) frictionScore += 0.15;
  if (payment.failureReason === 'AUTHENTICATION_FAILED') frictionScore += 0.08;
  const level = frictionScore > 0.47 ? 'High' : frictionScore > 0.3 ? 'Medium' : 'Low';
  return {
    agent: 'risk',
    title: 'Risk',
    finding: `Customer-friction risk assessed as ${level.toLowerCase()} for the proposed action.`,
    confidence: Math.round(jitter(0.85, 0.06) * 100),
    level,
    frictionScore,
    evidence: [
      `${payment.attempts} prior attempt${payment.attempts > 1 ? 's' : ''} already made`,
      `Candidate action: ${strategy.label.toLowerCase()}`,
      payment.amount > 40000 ? 'High-value payment — added sensitivity' : 'Standard-value payment',
    ],
  };
}

export function decideStrategy(payment, { prediction, economics, risk }) {
  const info = FAILURE_REASONS[payment.failureReason];
  let strategyKey = info.bestStrategy;
  let disagreement = null;
  const isRetryStrategy = strategyKey === 'immediate_retry' || strategyKey === 'delayed_retry';

  // Risk agent can override an aggressive prediction-favoured retry.
  if (risk.level === 'High' && isRetryStrategy) {
    if (payment.attempts >= 3) {
      disagreement = {
        from: 'Risk Agent',
        against: 'Prediction Agent',
        note: 'Further automated retries rejected after repeated friction on this payment — routed to a human specialist instead.',
      };
      strategyKey = 'escalation';
    } else {
      disagreement = {
        from: 'Risk Agent',
        against: 'Prediction Agent',
        note: `Prediction favoured acting now at ${Math.round(prediction.probability * 100)}% confidence, but Risk flagged high customer-friction from repeated attempts and delayed the action instead.`,
      };
      strategyKey = 'delayed_retry';
    }
  } else if (economics.expectedNet < 0) {
    disagreement = {
      from: 'Economics Agent',
      against: 'Strategy Agent',
      note: 'Expected net value is negative for the default action — recommending invoice recovery instead.',
    };
    strategyKey = 'invoice_recovery';
  }

  const strategy = STRATEGIES[strategyKey];
  const delayMinutes = strategyKey === 'delayed_retry' ? 15 + Math.floor(Math.random() * 340) : 0;

  return {
    agent: 'strategy',
    title: 'Strategy',
    strategyKey,
    finding: delayMinutes
      ? `${strategy.label} scheduled in ${delayMinutes} min to reach a higher-probability window.`
      : `${strategy.label} selected as the highest risk-adjusted expected value.`,
    confidence: Math.round(jitter(0.86, 0.05) * 100),
    delayMinutes,
    disagreement,
    evidence: [
      `Selected: ${strategy.label}`,
      `Expected net value: ₹${economics.expectedNet}`,
      `Friction risk: ${risk.level}`,
    ],
  };
}

export function runExecution(strategyKey) {
  const strategy = STRATEGIES[strategyKey];
  return {
    agent: 'execution',
    title: 'Execution',
    finding: `${strategy.label} executed against ${strategyKey === 'method_fallback' ? 'backup instrument' : 'payment processor'}.`,
    confidence: 100,
    evidence: [`Action: ${strategy.label}`, 'Executed via processor API (simulated)'],
  };
}

export function runVerification(payment, prediction, strategyKey) {
  const recovered = Math.random() < prediction.probability;
  const info = STRATEGIES[strategyKey];
  const recoveryTimeMinutes = strategyKey === 'delayed_retry'
    ? 20 + Math.floor(Math.random() * 300)
    : 1 + Math.floor(Math.random() * 40);
  const actualNet = recovered ? payment.amount - info.cost : -info.cost;
  return {
    agent: 'verification',
    title: 'Verification',
    finding: recovered
      ? `Payment confirmed recovered. Outcome fed back into the prediction model.`
      : `Payment remains unrecovered. Outcome logged for the next decision cycle.`,
    confidence: 100,
    recovered,
    actualNet,
    recoveryTimeMinutes,
    evidence: [
      recovered ? 'Processor confirmed settlement' : 'Processor confirmed continued decline',
      `Time to outcome: ${recoveryTimeMinutes} min`,
    ],
  };
}

export function requiresApproval(payment, decision, controls) {
  if (!controls.autoExecute) return true;
  if (decision.strategyKey === 'escalation' || decision.strategyKey === 'human_review') return true;
  if (payment.amount >= controls.highValueThreshold) return true;
  if (decision.confidence < controls.confidenceThreshold) return true;
  return false;
}
