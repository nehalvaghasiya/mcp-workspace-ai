import { type Artifact } from '@mcp-workspace/shared-types';
import { Download, FileText } from 'lucide-react';
import { formatBytes, formatDate } from '../../lib/format';
import { safeDownloadUrl } from '../../lib/urls';
import { Sources } from '../chat/Sources';
import { Chip } from '../ui/Chip';

export function ArtifactCard({
  artifact,
  onDelete,
}: {
  artifact: Artifact;
  onDelete?: () => void;
}) {
  const download = safeDownloadUrl(artifact.download_url);
  return (
    <article className="artifact-card">
      <div className={`file-icon ${artifact.format}`}>
        <FileText size={22} aria-hidden="true" />
        <span>{artifact.format.toUpperCase()}</span>
      </div>
      <div className="artifact-info">
        <h3>{artifact.title}</h3>
        <p>
          {formatBytes(artifact.size)} <span>·</span> {artifact.mime_type}
        </p>
        <Chip tone={artifact.validated ? 'positive' : 'warning'}>
          {artifact.validated ? 'Readback validated' : 'Validation unavailable'}
        </Chip>
        <details>
          <summary>File details & sources</summary>
          <dl>
            <dt>Created</dt>
            <dd>{formatDate(artifact.created_at)}</dd>
            <dt>SHA-256</dt>
            <dd className="hash">{artifact.sha256}</dd>
          </dl>
          <Sources sources={artifact.sources ?? []} />
        </details>
      </div>
      <div className="artifact-actions">
        {download ? (
          <a
            className="icon-button"
            href={download}
            download
            aria-label={`Download ${artifact.title}`}
          >
            <Download size={18} />
          </a>
        ) : (
          <span className="muted">Download unavailable</span>
        )}
        {onDelete && (
          <button className="text-button danger" onClick={onDelete}>
            Delete
          </button>
        )}
      </div>
    </article>
  );
}
