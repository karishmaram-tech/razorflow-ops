import { Link } from 'react-router-dom';
import { ArrowRight, FlaskConical } from 'lucide-react';
import Button from '../ui/Button';
import HeroPipelineVisual from './HeroPipelineVisual';

export default function Hero() {
  return (
    <section id="product" className="mx-auto grid max-w-[1200px] grid-cols-1 items-center gap-10 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:px-8 lg:py-24">
      <div>
        <p className="text-[13px] font-medium uppercase tracking-wide text-[var(--color-ink-faint)]">RecoveryFlow</p>
        <h1 className="mt-2 text-[34px] font-semibold leading-[1.15] text-[var(--color-ink)] sm:text-[42px]">
          Autonomous revenue recovery for failed payments.
        </h1>
        <p className="mt-4 max-w-lg text-[15.5px] leading-relaxed text-[var(--color-ink-soft)]">
          Don't just retry failed payments — decide which ones are worth saving, and how. RecoveryFlow
          investigates every failure, predicts recovery probability, weighs the economics and the risk,
          picks a strategy, executes it, verifies the outcome, and learns from every result.
        </p>
        <div className="mt-7 flex flex-wrap items-center gap-3">
          <Link to="/app">
            <Button size="lg" icon={ArrowRight}>Enter RecoveryFlow</Button>
          </Link>
          <a href="#how-it-works">
            <Button size="lg" variant="secondary">Explore the system</Button>
          </a>
          <Link to="/app/sandbox" className="flex items-center gap-1.5 px-2 text-[13.5px] font-medium text-[var(--color-ink-soft)] hover:text-[var(--color-ink)]">
            <FlaskConical size={15} />
            Open Sandbox
          </Link>
        </div>
      </div>

      <div className="flex justify-center lg:justify-end">
        <HeroPipelineVisual />
      </div>
    </section>
  );
}
