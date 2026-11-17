import { type WorkspaceFile } from '@mcp-workspace/shared-types';
import { ExternalLink, FileText, Presentation, Sheet } from 'lucide-react';
import { formatDate } from '../../lib/format';
import { safeGoogleFileUrl } from '../../lib/urls';
import { Chip } from '../ui/Chip';

export function WorkspaceFileCard({ file }: { file: WorkspaceFile }) {
  const url = safeGoogleFileUrl(file.web_url);
  const Icon = file.kind === 'sheets' ? Sheet : file.kind === 'slides' ? Presentation : FileText;
  const name =
    file.kind === 'sheets'
      ? 'Google Sheets'
      : file.kind === 'slides'
        ? 'Google Slides'
        : 'Google Docs';
  return (
    <article className="artifact-card">
      <div className={`file-icon ${file.kind}`}>
        <Icon size={22} aria-hidden="true" />
        <span>{file.kind.toUpperCase()}</span>
      </div>
      <div className="artifact-info">
        <h3>{file.title}</h3>
        <p>
          {name} <span>·</span> Updated {formatDate(file.updated_at)}
        </p>
        <Chip tone={file.status === 'ready' ? 'positive' : 'warning'}>
          {file.status === 'ready'
            ? 'Google readback verified'
            : file.status === 'partial'
              ? 'Partially created · review in Google'
              : 'Readback not verified'}
        </Chip>
        {file.status === 'partial' && (
          <p>Some requested content could not be saved. Review the file before retrying.</p>
        )}
      </div>
      <div className="artifact-actions">
        {url ? (
          <a
            className="icon-button"
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={`Open ${file.title} in Google`}
          >
            <ExternalLink size={18} />
          </a>
        ) : (
          <span className="muted">Google link unavailable</span>
        )}
      </div>
    </article>
  );
}
