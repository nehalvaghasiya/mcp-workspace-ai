import { type SourceRef } from '@mcp-workspace/shared-types';
import { ArrowUpRight } from 'lucide-react';
import { formatDate } from '../../lib/format';
import { safeSourceUrl } from '../../lib/urls';

export function Sources({ sources }: { sources: SourceRef[] }) {
  if (!sources.length) return null;
  return (
    <div className="sources">
      <h4>
        Sources <span>{sources.length}</span>
      </h4>
      <div className="source-list">
        {sources.map((source) => {
          const url = safeSourceUrl(source.url);
          return (
            <details className="source" key={`${source.provider}:${source.resource_id}`}>
              <summary>
                <span className={`provider-dot ${source.provider}`} />
                <span className="source-title">{source.title}</span>
                <span className="source-provider">{source.provider}</span>
              </summary>
              <div className="source-body">
                {source.snippet && <p>{source.snippet}</p>}
                <dl>
                  <dt>Resource</dt>
                  <dd>{source.resource_id}</dd>
                  <dt>Retrieved</dt>
                  <dd>{formatDate(source.retrieved_at)}</dd>
                  {source.pointer && (
                    <>
                      <dt>Reference</dt>
                      <dd>{source.pointer}</dd>
                    </>
                  )}
                </dl>
                {url ? (
                  <a href={url} target="_blank" rel="noopener noreferrer">
                    Open source <ArrowUpRight size={14} />
                  </a>
                ) : (
                  <span className="muted">
                    {source.resource_id.startsWith('mock-')
                      ? 'Synthetic demo source · no external link'
                      : 'No provider link available'}
                  </span>
                )}
              </div>
            </details>
          );
        })}
      </div>
    </div>
  );
}
