import { createContext, useContext, useEffect, useMemo, useReducer, useRef } from 'react';
import {
  createPayment,
  runInvestigation,
  runPrediction,
  runEconomics,
  runRisk,
  decideStrategy,
  runExecution,
  runVerification,
  requiresApproval,
} from './engine';
import { FAILURE_REASONS, STRATEGIES, SCENARIOS } from './domain';

const RecoveryStateContext = createContext(null);
const RecoveryDispatchContext = createContext(null);

const DEFAULT_CONTROLS = {
  maxRetryAttempts: 3,
  maxInterventionCost: 60,
  customerContactLimit: 2,
  confidenceThreshold: 70,
  highValueThreshold: 40000,
  humanApprovalThreshold: 40000,
  autoExecute: true,
};

function tagTrace(entry) {
  return { ...entry, timestamp: new Date() };
}

function advancePayment(payment, controls) {
  const now = new Date();
  switch (payment.stage) {
    case 'queued': {
      const investigation = runInvestigation(payment);
      return {
        ...payment,
        stage: 'investigating',
        investigation,
        stageEnteredAt: now,
        trace: [...payment.trace, tagTrace(investigation)],
      };
    }
    case 'investigating': {
      const prediction = runPrediction(payment);
      return {
        ...payment,
        stage: 'predicting',
        prediction,
        stageEnteredAt: now,
        trace: [...payment.trace, tagTrace(prediction)],
      };
    }
    case 'predicting': {
      const info = FAILURE_REASONS[payment.failureReason];
      const economics = runEconomics(payment, payment.prediction, info.bestStrategy);
      const risk = runRisk(payment, payment.prediction, info.bestStrategy);
      return {
        ...payment,
        stage: 'evaluating',
        economics,
        risk,
        stageEnteredAt: now,
        trace: [...payment.trace, tagTrace(economics), tagTrace(risk)],
      };
    }
    case 'evaluating': {
      const decision = decideStrategy(payment, {
        prediction: payment.prediction,
        economics: payment.economics,
        risk: payment.risk,
      });
      const needsApproval = requiresApproval(payment, decision, controls);
      return {
        ...payment,
        stage: needsApproval ? 'awaiting_approval' : 'executing',
        decision,
        stageEnteredAt: now,
        trace: [...payment.trace, tagTrace(decision)],
      };
    }
    case 'awaiting_approval':
      return payment;
    case 'executing': {
      const execution = runExecution(payment.decision.strategyKey);
      return {
        ...payment,
        stage: 'verifying',
        stageEnteredAt: now,
        trace: [...payment.trace, tagTrace(execution)],
      };
    }
    case 'verifying': {
      const verification = runVerification(payment, payment.prediction, payment.decision.strategyKey);
      return {
        ...payment,
        stage: 'resolved',
        outcome: verification,
        resolvedAt: now,
        stageEnteredAt: now,
        trace: [...payment.trace, tagTrace(verification)],
      };
    }
    default:
      return payment;
  }
}

function activityFromPayment(prevPayment, nextPayment) {
  if (nextPayment.trace.length === prevPayment.trace.length) return [];
  const added = nextPayment.trace.slice(prevPayment.trace.length);
  return added.map((entry) => ({
    id: `${nextPayment.id}-${entry.agent}-${entry.timestamp.getTime()}-${Math.random().toString(36).slice(2, 7)}`,
    paymentId: nextPayment.id,
    timestamp: entry.timestamp,
    text: `${entry.title} — ${entry.finding}`,
    agent: entry.agent,
  }));
}

function auditFromPayment(nextPayment) {
  const entries = [];
  if (nextPayment.stage === 'executing' && nextPayment.decision) {
    entries.push({
      id: `${nextPayment.id}-decision-${Date.now()}`,
      timestamp: new Date(),
      paymentId: nextPayment.id,
      agent: 'Strategy Agent',
      decision: STRATEGIES[nextPayment.decision.strategyKey].label,
      reason: nextPayment.decision.finding,
      action: 'Approved for execution',
      outcome: 'Pending',
    });
  }
  if (nextPayment.stage === 'resolved' && nextPayment.outcome) {
    entries.push({
      id: `${nextPayment.id}-outcome-${Date.now()}`,
      timestamp: new Date(),
      paymentId: nextPayment.id,
      agent: 'Verification Agent',
      decision: STRATEGIES[nextPayment.decision.strategyKey].label,
      reason: nextPayment.outcome.recovered
        ? 'Processor confirmed settlement'
        : 'Processor confirmed continued decline',
      action: 'Verified outcome',
      outcome: nextPayment.outcome.recovered ? 'Recovered' : 'Not recovered',
    });
  }
  return entries;
}

const initialState = {
  payments: [],
  activity: [],
  audit: [],
  controls: DEFAULT_CONTROLS,
  isRunning: true,
  fastForward: false,
  demoMode: false,
  demoBatchIds: [],
  demoResult: null,
  clockTick: 0,
};

function scenarioOptions(scenarioKey) {
  const scenario = SCENARIOS.find((s) => s.key === scenarioKey) || SCENARIOS[0];
  const options = {};
  if (scenario.reason) options.forceReason = scenario.reason;
  if (scenario.forceAttempts) options.forceAttempts = scenario.forceAttempts;
  if (scenario.forceHighValue) options.forceHighValue = true;
  if (scenario.forceLowValue) options.forceLowValue = true;
  return options;
}

function seedPayments() {
  const payments = [];
  const now = Date.now();
  for (let i = 0; i < 6; i += 1) {
    let p = createPayment(new Date(now - i * 40000));
    // fast-forward some seeded payments a bit so the board isn't empty on load
    const steps = i % 3;
    for (let s = 0; s < steps; s += 1) {
      p = advancePayment(p, DEFAULT_CONTROLS);
    }
    payments.push(p);
  }
  return payments;
}

function reducer(state, action) {
  switch (action.type) {
    case 'TICK': {
      const controls = state.controls;
      const newActivity = [];
      const newAudit = [];
      let payments = state.payments.map((p) => {
        if (p.stage === 'resolved' || p.stage === 'awaiting_approval') return p;
        // stagger progression so payments don't all move in perfect lockstep
        if (Math.random() < 0.22) return p;
        const next = advancePayment(p, controls);
        newActivity.push(...activityFromPayment(p, next));
        newAudit.push(...auditFromPayment(next));
        return next;
      });

      // occasionally spawn a new failed payment
      const activeCount = payments.filter((p) => p.stage !== 'resolved').length;
      if (state.isRunning && activeCount < 22 && Math.random() < (state.demoMode ? 0 : 0.3)) {
        const fresh = createPayment(new Date());
        payments = [fresh, ...payments];
        newActivity.unshift({
          id: `${fresh.id}-spawn-${Date.now()}`,
          paymentId: fresh.id,
          timestamp: new Date(),
          text: `Payment failure detected — ₹${fresh.amount.toLocaleString('en-IN')}`,
          agent: 'system',
        });
      }

      let demoMode = state.demoMode;
      let demoResult = state.demoResult;
      if (demoMode) {
        const batch = payments.filter((p) => state.demoBatchIds.includes(p.id));
        const allResolved = batch.length > 0 && batch.every((p) => p.stage === 'resolved' || p.stage === 'awaiting_approval');
        if (allResolved) {
          const recovered = batch.filter((p) => p.outcome?.recovered);
          const totalAmount = batch.reduce((s, p) => s + p.amount, 0);
          const recoveredAmount = recovered.reduce((s, p) => s + p.amount, 0);
          const netRecovery = recovered.reduce((s, p) => s + (p.outcome?.actualNet || 0), 0)
            - batch.filter((p) => !p.outcome?.recovered && p.outcome).reduce((s, p) => s + Math.abs(p.outcome.actualNet || 0), 0);
          const delayedCount = batch.filter((p) => p.decision?.strategyKey === 'delayed_retry').length;
          const immediateCount = batch.filter((p) => p.decision?.strategyKey === 'immediate_retry').length;
          const delayedRecovered = batch.filter((p) => p.decision?.strategyKey === 'delayed_retry' && p.outcome?.recovered).length;
          const immediateRecovered = batch.filter((p) => p.decision?.strategyKey === 'immediate_retry' && p.outcome?.recovered).length;
          const delayedRate = delayedCount ? (delayedRecovered / delayedCount) * 100 : 0;
          const immediateRate = immediateCount ? (immediateRecovered / immediateCount) * 100 : 0;
          demoResult = {
            totalAmount,
            recoveredAmount,
            recoveryRate: (recovered.length / batch.length) * 100,
            netRecovery,
            delayedRate,
            immediateRate,
            escalated: batch.filter((p) => p.decision?.strategyKey === 'escalation').length,
            awaitingApproval: batch.filter((p) => p.stage === 'awaiting_approval').length,
          };
          demoMode = false;
        }
      }

      return {
        ...state,
        payments,
        activity: [...newActivity, ...state.activity].slice(0, 60),
        audit: [...newAudit, ...state.audit].slice(0, 120),
        demoMode,
        demoResult,
        clockTick: state.clockTick + 1,
      };
    }
    case 'APPROVE_PAYMENT': {
      const payments = state.payments.map((p) => (p.id === action.id && p.stage === 'awaiting_approval'
        ? { ...p, stage: 'executing', stageEnteredAt: new Date() }
        : p));
      const audit = [{
        id: `${action.id}-approve-${Date.now()}`,
        timestamp: new Date(),
        paymentId: action.id,
        agent: 'Operator',
        decision: 'Manual approval',
        reason: 'Approved by operator for execution',
        action: 'Approved',
        outcome: 'Proceeding to execution',
      }, ...state.audit];
      return { ...state, payments, audit };
    }
    case 'REJECT_PAYMENT': {
      const payments = state.payments.map((p) => (p.id === action.id && p.stage === 'awaiting_approval'
        ? {
          ...p,
          stage: 'resolved',
          resolvedAt: new Date(),
          outcome: { recovered: false, actualNet: 0, recoveryTimeMinutes: 0, rejected: true },
        }
        : p));
      const audit = [{
        id: `${action.id}-reject-${Date.now()}`,
        timestamp: new Date(),
        paymentId: action.id,
        agent: 'Operator',
        decision: 'Manual rejection',
        reason: 'Rejected by operator — no automated action taken',
        action: 'Rejected',
        outcome: 'Held, no action taken',
      }, ...state.audit];
      return { ...state, payments, audit };
    }
    case 'UPDATE_CONTROLS':
      return { ...state, controls: { ...state.controls, ...action.payload } };
    case 'TOGGLE_RUNNING':
      return { ...state, isRunning: !state.isRunning };
    case 'SET_SPEED':
      return { ...state, fastForward: action.fast };
    case 'GENERATE_PAYMENT': {
      const fresh = createPayment(new Date(), { ...scenarioOptions(action.scenario), origin: 'sandbox' });
      const activity = [{
        id: `${fresh.id}-spawn-${Date.now()}`,
        paymentId: fresh.id,
        timestamp: new Date(),
        text: `Synthetic payment failure generated — ₹${fresh.amount.toLocaleString('en-IN')}`,
        agent: 'system',
      }, ...state.activity].slice(0, 60);
      return { ...state, payments: [fresh, ...state.payments], activity, isRunning: true };
    }
    case 'GENERATE_BATCH': {
      const now = Date.now();
      const opts = scenarioOptions(action.scenario);
      const batch = Array.from({ length: action.count || 10 }, (_, i) => createPayment(new Date(now - i * 200), { ...opts, origin: 'sandbox' }));
      const activity = [{
        id: `batch-${now}`,
        paymentId: null,
        timestamp: new Date(),
        text: `Synthetic batch generated — ${batch.length} payments`,
        agent: 'system',
      }, ...state.activity].slice(0, 60);
      return { ...state, payments: [...batch, ...state.payments], activity, isRunning: true };
    }
    case 'RESET_SIMULATION':
      return {
        ...initialState,
        controls: state.controls,
        payments: [],
        activity: [],
        audit: [],
      };
    case 'START_RECOVERY': {
      const now = Date.now();
      const opts = scenarioOptions(action.scenario);
      const batch = Array.from({ length: action.count || 14 }, (_, i) => createPayment(new Date(now - i * 500), { ...opts, origin: 'sandbox' }));
      return {
        ...state,
        payments: [...batch, ...state.payments],
        demoMode: true,
        demoBatchIds: batch.map((p) => p.id),
        demoResult: null,
        isRunning: true,
      };
    }
    case 'DISMISS_DEMO_RESULT':
      return { ...state, demoResult: null };
    default:
      return state;
  }
}

export function RecoveryProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState, (init) => ({
    ...init,
    payments: seedPayments(),
  }));
  const intervalRef = useRef(null);

  useEffect(() => {
    const speed = (state.demoMode || state.fastForward) ? 420 : 2400;
    intervalRef.current = setInterval(() => {
      if (state.isRunning) dispatch({ type: 'TICK' });
    }, speed);
    return () => clearInterval(intervalRef.current);
  }, [state.isRunning, state.demoMode, state.fastForward]);

  return (
    <RecoveryStateContext.Provider value={state}>
      <RecoveryDispatchContext.Provider value={dispatch}>
        {children}
      </RecoveryDispatchContext.Provider>
    </RecoveryStateContext.Provider>
  );
}

export function useRecoveryState() {
  const ctx = useContext(RecoveryStateContext);
  if (!ctx) throw new Error('useRecoveryState must be used within RecoveryProvider');
  return ctx;
}

export function useRecoveryDispatch() {
  const ctx = useContext(RecoveryDispatchContext);
  if (!ctx) throw new Error('useRecoveryDispatch must be used within RecoveryProvider');
  return ctx;
}

export function useMetrics() {
  const { payments } = useRecoveryState();
  return useMemo(() => {
    const resolved = payments.filter((p) => p.stage === 'resolved');
    const recovered = resolved.filter((p) => p.outcome?.recovered);
    const unrecovered = resolved.filter((p) => p.outcome && !p.outcome.recovered);
    const active = payments.filter((p) => p.stage !== 'resolved');

    const grossVolume = payments.reduce((s, p) => s + p.amount, 0);
    const recoveredRevenue = recovered.reduce((s, p) => s + p.amount, 0);
    const revenueAtRisk = active.reduce((s, p) => s + p.amount, 0) + unrecovered.reduce((s, p) => s + p.amount, 0);
    const expectedRecovery = active.reduce((s, p) => s + (p.prediction ? p.prediction.probability * p.amount : p.amount * 0.55), 0);
    const netRecovery = recovered.reduce((s, p) => s + (p.outcome?.actualNet || 0), 0)
      - unrecovered.reduce((s, p) => s + Math.abs(p.outcome?.actualNet || 0), 0);
    const totalCost = resolved.reduce((s, p) => s + (p.decision ? STRATEGIES[p.decision.strategyKey].cost : 0), 0);
    const recoveryRate = resolved.length ? (recovered.length / resolved.length) * 100 : 0;
    // Expressed as a multiplier (net recovered per rupee spent on action cost),
    // not a percentage — retry-style actions cost pennies against recovered
    // revenue, so a percentage reads as an error rather than a real number.
    const roi = totalCost > 0 ? netRecovery / totalCost : 0;
    const awaitingApproval = payments.filter((p) => p.stage === 'awaiting_approval').length;

    return {
      grossVolume,
      revenueAtRisk,
      expectedRecovery,
      recoveredRevenue,
      netRecovery,
      recoveryRate,
      roi,
      awaitingApproval,
      resolvedCount: resolved.length,
      activeCount: active.length,
      recoveredCount: recovered.length,
    };
  }, [payments]);
}
