import { Boxes, Check, LayoutDashboard, ShieldCheck, X } from 'lucide-react';
import { useConversation } from '../../features/conversations/useConversation';
import { ToolTimeline } from '../mcp-explorer/ToolTimeline';
import { Chip } from '../ui/Chip';
import { Empty } from '../ui/Empty';
import { ErrorNotice } from '../ui/ErrorNotice';

type ActivityProps = Pick<
  ReturnType<typeof useConversation>,
  'hasMessages' | 'runId' | 'active' | 'currentLive' | 'lastRun' | 'timeline' | 'trace'
> & { onClose: () => void };

export function ActivityPanel({
  hasMessages,
  runId,
  active,
  currentLive,
  lastRun,
  timeline,
  trace,
  onClose,
}: ActivityProps) {
  return (
    <aside
      className={`activity-panel ${hasMessages ? 'has-messages' : ''}`}
      aria-label="Run activity"
    >
      <div className="activity-heading">
        <span>
          <LayoutDashboard size={16} />
          Activity
        </span>
        <button className="icon-button" aria-label="Hide activity" onClick={() => onClose()}>
          <X size={16} />
        </button>
      </div>
      {runId ? (
        <>
          <div className="activity-run">
            <span className="eyebrow">CURRENT RUN</span>
            <code title={runId}>{runId.slice(0, 16)}</code>
            <Chip
              tone={
                active
                  ? 'warning'
                  : ['failed', 'interrupted'].includes(lastRun?.status ?? '')
                    ? 'negative'
                    : lastRun?.status === 'completed'
                      ? 'positive'
                      : ''
              }
            >
              {currentLive?.finished
                ? currentLive.events.at(-1)?.type.replace('run.', '').replaceAll('_', ' ')
                : lastRun?.status.replaceAll('_', ' ')}
            </Chip>
          </div>
          {active && (
            <p className="activity-model" role="status">
              {currentLive?.events.at(-1)?.type === 'model.started'
                ? 'Model is responding…'
                : 'Working through your request…'}
            </p>
          )}
          <ToolTimeline traces={timeline} />
          {trace.isError && <ErrorNotice error={trace.error} retry={() => void trace.refetch()} />}
          {!timeline.length && (
            <Empty title="No tool calls recorded">
              Tool activity appears here as the server executes it.
            </Empty>
          )}
        </>
      ) : (
        <div className="activity-empty">
          <div className="activity-orbit">
            <Boxes size={25} />
          </div>
          <h3>Every step, in the open.</h3>
          <p>Tools, sources, and decisions appear here as your request takes shape.</p>
          <div className="activity-legend">
            <span>
              <span className="legend-dot" />
              Connected tools
            </span>
            <span>
              <span className="legend-dot amber" />
              Your approval
            </span>
            <span>
              <Check size={13} />
              Verified results
            </span>
          </div>
        </div>
      )}
      <div className="activity-bottom">
        <ShieldCheck size={15} />
        <p>External actions pause for your approval. Tool inputs and results are inspectable.</p>
      </div>
    </aside>
  );
}
