import { AlertCircle, RotateCcw } from 'lucide-react';
import { type Run } from '@mcp-workspace/shared-types';
import { Sources } from './Sources';

export function RunFailure({
  run,
  pending,
  online,
  onRetry,
  onActivity,
}: {
  run: Run;
  pending: boolean;
  online: boolean;
  onRetry: () => void;
  onActivity: () => void;
}) {
  return (
    <div className="run-failure" role="alert">
      <div className="run-failure-heading">
        <AlertCircle size={20} />
        <strong>Response incomplete</strong>
      </div>
      <p>{run.error || 'This run stopped before completing. Your completed steps are saved.'}</p>
      {!!run.read_count && (
        <p className="run-progress">
          Read {run.read_count}
          {run.selected_count != null ? ` of ${run.selected_count}` : ''} messages. Retrieved
          sources are saved.
        </p>
      )}
      <div className="inline-actions">
        {run.retryable && (
          <button className="button" disabled={pending || !online} onClick={onRetry}>
            <RotateCcw size={15} />
            {pending ? 'Continuing…' : 'Continue from saved progress'}
          </button>
        )}
        <button className="text-button" onClick={onActivity}>
          Review activity
        </button>
      </div>
      {run.error_code && (
        <details>
          <summary>Technical details</summary>
          <code>{run.error_code}</code>
        </details>
      )}
      <Sources sources={run.sources ?? []} />
    </div>
  );
}
