import { type Approval } from '@mcp-workspace/shared-types';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { CircleCheck, ShieldCheck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { formatDate } from '../../lib/format';
import { api } from '../../services/api';
import { Chip } from '../ui/Chip';
import { ErrorNotice } from '../ui/ErrorNotice';
import { JsonBlock } from '../ui/JsonBlock';
import { Spinner } from '../ui/Spinner';

export function ApprovalCard({
  approval,
  onDecision,
}: {
  approval: Approval;
  onDecision?: () => void;
}) {
  const client = useQueryClient();
  const [now, setNow] = useState(Date.now);
  const [decided, setDecided] = useState<string>();
  useEffect(() => {
    const interval = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(interval);
  }, []);
  const expiration = Date.parse(approval.expires_at);
  const expired = !Number.isFinite(expiration) || expiration <= now;
  const pending = approval.status === 'pending' && !expired && !decided;
  const fields = {
    ...(typeof approval.summary === 'object' ? approval.summary : {}),
    ...approval.arguments,
  };
  const actionTitles: Record<string, string> = {
    'gmail.create_draft': 'Create this email draft',
    'gmail.send_draft': 'Send this email',
    'calendar.create_event': 'Create this calendar event',
    'calendar.update_event': 'Update this calendar event',
    'calendar.cancel_event': 'Cancel this calendar event',
    'drive.upload_artifact': 'Upload this file to Drive',
    'drive.share_file': 'Share this Drive file',
  };
  const title =
    typeof approval.summary === 'string'
      ? approval.summary
      : (actionTitles[approval.tool] ?? `Review ${approval.tool}`);
  const decision = useMutation({
    mutationFn: (choice: 'approve' | 'reject') => api.decide(approval.id, choice),
    onSuccess: (value) => {
      setDecided(value.status);
      void client.invalidateQueries({ queryKey: ['approvals'] });
      void client.invalidateQueries({ queryKey: ['conversations'] });
      void client.invalidateQueries({ queryKey: ['conversation'] });
      onDecision?.();
    },
  });
  return (
    <article className="approval-card">
      <div className="approval-title">
        <span className="approval-icon">
          <ShieldCheck size={20} />
        </span>
        <div>
          <span className="eyebrow">{pending ? 'YOUR APPROVAL IS REQUIRED' : 'ACTION REVIEW'}</span>
          <h3>{title}</h3>
        </div>
        <Chip tone={pending ? 'warning' : ''}>
          {(approval.status === 'pending' ? decided : undefined) ??
            (expired && approval.status === 'pending' ? 'Expired' : approval.status)}
        </Chip>
      </div>
      <p className="approval-tool">{approval.tool}</p>
      <dl className="action-fields">
        {Object.entries(fields).map(([key, value]) => (
          <div key={key}>
            <dt>{key.replaceAll('_', ' ')}</dt>
            <dd>
              {typeof value === 'string' && value.length > 500 ? (
                <>
                  <p>{value.slice(0, 120)}…</p>
                  <details className="approval-body">
                    <summary>
                      Read exact {key.replaceAll('_', ' ')} · {value.length.toLocaleString()}{' '}
                      characters
                    </summary>
                    <div className="approval-body-text" tabIndex={0}>
                      {value}
                    </div>
                  </details>
                </>
              ) : typeof value === 'string' ? (
                value
              ) : Array.isArray(value) && value.every((item) => typeof item === 'string') ? (
                value.length ? (
                  value.join('\n')
                ) : (
                  'None'
                )
              ) : (
                <JsonBlock value={value} />
              )}
            </dd>
          </div>
        ))}
      </dl>
      <details className="approval-details">
        <summary>Approval identity and expiration</summary>
        <dl>
          <dt>Action digest</dt>
          <dd className="hash">{approval.action_digest}</dd>
          <dt>Expires</dt>
          <dd>{formatDate(approval.expires_at)}</dd>
          <dt>Run</dt>
          <dd>{approval.run_id}</dd>
        </dl>
      </details>
      {pending && (
        <p className="approval-disclosure">
          Approving executes this exact action once. Any changed parameters need a new approval.
        </p>
      )}
      <div className="approval-actions">
        <button
          className="button"
          disabled={!pending || decision.isPending}
          onClick={() => decision.mutate('reject')}
        >
          Reject
        </button>
        <button
          className="button primary"
          disabled={!pending || decision.isPending}
          onClick={() => decision.mutate('approve')}
        >
          {decision.isPending ? (
            <Spinner label="Submitting decision" />
          ) : (
            <>
              <CircleCheck size={16} />
              Approve exact action
            </>
          )}
        </button>
      </div>
      {decision.isError && (
        <ErrorNotice
          error={decision.error}
          retry={() => void client.invalidateQueries({ queryKey: ['approvals'] })}
        />
      )}
    </article>
  );
}
