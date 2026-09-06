import { Link } from 'react-router-dom';
import { ArrowRight, FlaskConical } from 'lucide-react';
import Button from '../ui/Button';

export default function FinalCta() {
  return (
    <section className="border-t border-[var(--color-line)] bg-[var(--color-navy-900)] py-16">
      <div className="mx-auto max-w-[800px] px-4 text-center sm:px-6 lg:px-8">
        <h2 className="text-[26px] font-semibold text-white sm:text-[30px]">
          Recover the right payments. Not just more payments.
        </h2>
        <p className="mx-auto mt-3 max-w-lg text-[14.5px] leading-relaxed text-white/60">
          RecoveryFlow turns failed payment events into autonomous, measurable recovery decisions.
        </p>
        <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
          <Link to="/app">
            <Button size="lg" icon={ArrowRight}>Enter RecoveryFlow</Button>
          </Link>
          <Link to="/app/sandbox">
            <Button size="lg" variant="secondary" icon={FlaskConical} className="border-white/20 bg-white/5 text-white hover:bg-white/10">
              Explore Sandbox
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
}
