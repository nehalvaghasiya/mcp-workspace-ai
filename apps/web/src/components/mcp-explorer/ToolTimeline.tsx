import { type ToolTrace } from '@mcp-workspace/shared-types';
import { Check, Clock3 } from 'lucide-react';
import { Sources } from '../chat/Sources';
import { JsonBlock } from '../ui/JsonBlock';

export function ToolTimeline({ traces }: { traces: ToolTrace[] }) {
  return (
    <ol className="tool-timeline">
      {traces.map((trace, index) => (
        <li key={trace.id ?? `${trace.tool}-${index}`}>
          <span
            className={`timeline-marker ${trace.status === 'running' ? 'working' : trace.status === 'failed' || trace.error ? 'failed' : ''}`}
          >
            {trace.status === 'running' ? <Clock3 size={12} /> : <Check size={12} />}
          </span>
          <details className="tool-step">
            <summary>
              <span className="tool-server">{trace.server}</span>
              <strong>
                {trace.tool.includes('.') ? trace.tool.split('.').slice(1).join('.') : trace.tool}
              </strong>
              <span className="tool-step-meta">
                {trace.error ? 'Failed' : (trace.status ?? 'completed')}
                {trace.elapsed_ms !== undefined && <> · {Math.round(trace.elapsed_ms)} ms</>}
              </span>
            </summary>
            <div className="tool-detail">
              <p className="eyebrow">INPUT</p>
              <JsonBlock value={trace.arguments ?? {}} />
              {trace.data !== undefined && (
                <>
                  <p className="eyebrow">RESULT</p>
                  <JsonBlock value={trace.data} />
                </>
              )}
              {trace.error && <p className="danger">{trace.error}</p>}
              {!!trace.sources?.length && <Sources sources={trace.sources} />}
            </div>
          </details>
        </li>
      ))}
    </ol>
  );
}
