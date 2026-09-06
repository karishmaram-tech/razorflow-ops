import PublicNav from '../components/homepage/PublicNav';
import Hero from '../components/homepage/Hero';
import ProblemSection from '../components/homepage/ProblemSection';
import HowItThinks from '../components/homepage/HowItThinks';
import AgentDisagreementShowcase from '../components/homepage/AgentDisagreementShowcase';
import ProductPreview from '../components/homepage/ProductPreview';
import TrustSection from '../components/homepage/TrustSection';
import AuditabilitySection from '../components/homepage/AuditabilitySection';
import FinalCta from '../components/homepage/FinalCta';
import Footer from '../components/homepage/Footer';

export default function Homepage() {
  return (
    <div className="min-h-screen bg-[var(--color-paper)]">
      <PublicNav />
      <Hero />
      <ProblemSection />
      <HowItThinks />
      <AgentDisagreementShowcase />
      <ProductPreview />
      <TrustSection />
      <AuditabilitySection />
      <FinalCta />
      <Footer />
    </div>
  );
}
