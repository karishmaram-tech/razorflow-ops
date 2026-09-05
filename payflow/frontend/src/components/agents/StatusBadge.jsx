import Badge from '../ui/Badge';
import { stageStatusLabel } from '../../lib/stages';

export default function StatusBadge({ payment }) {
  const label = stageStatusLabel(payment);
  let variant = 'neutral';
  if (payment.stage === 'awaiting_approval') variant = 'warning';
  else if (payment.stage === 'resolved') {
    if (payment.outcome?.rejected) variant = 'neutral';
    else variant = payment.outcome?.recovered ? 'success' : 'danger';
  } else if (payment.stage !== 'queued') variant = 'info';

  return <Badge variant={variant} dot>{label}</Badge>;
}
