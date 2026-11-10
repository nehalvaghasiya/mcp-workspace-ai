import { useQuery } from '@tanstack/react-query';
import { ShieldCheck } from 'lucide-react';
import { ApprovalCard } from '../../components/approvals/ApprovalCard';
import { PageHeading } from '../../components/layout/PageHeading';
import { Empty } from '../../components/ui/Empty';
import { ErrorNotice } from '../../components/ui/ErrorNotice';
import { Spinner } from '../../components/ui/Spinner';
import { api } from '../../services/api';

export function ApprovalsPage() {
  const approvals = useQuery({
    queryKey: ['approvals'],
    queryFn: ({ signal }) => api.approvals(signal),
    refetchInterval: 4000,
  });
  return (
    <>
      <PageHeading
        eyebrow="YOU MAKE THE CALL"
        title="A moment to review. Then move forward."
        description="Review exact recipients, content, destinations, and side effects before an action runs."
      />
      {approvals.isPending ? (
        <Spinner label="Loading action reviews" />
      ) : approvals.isError ? (
        <ErrorNotice error={approvals.error} retry={() => void approvals.refetch()} />
      ) : approvals.data.length ? (
        <div className="approval-list">
          {approvals.data.map((approval) => (
            <ApprovalCard key={approval.id} approval={approval} />
          ))}
        </div>
      ) : (
        <Empty title="Nothing waiting on your approval">
          When a request involves sending, inviting, sharing, or another protected action, its exact
          details will appear here.
        </Empty>
      )}
      <div className="page-footnote">
        <ShieldCheck size={15} />
        Approvals expire and apply to one exact action. Closing this page never approves anything.
      </div>
    </>
  );
}
