import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { FileText } from 'lucide-react';
import { useState } from 'react';
import { ArtifactCard } from '../../components/artifacts/ArtifactCard';
import { WorkspaceFileCard } from '../../components/artifacts/WorkspaceFileCard';
import { PageHeading } from '../../components/layout/PageHeading';
import { Empty } from '../../components/ui/Empty';
import { ErrorNotice } from '../../components/ui/ErrorNotice';
import { Spinner } from '../../components/ui/Spinner';
import { api } from '../../services/api';

export function ArtifactsPage() {
  const client = useQueryClient();
  const artifacts = useQuery({
    queryKey: ['artifacts'],
    queryFn: ({ signal }) => api.artifacts(signal),
  });
  const workspaceFiles = useQuery({
    queryKey: ['workspace-files'],
    queryFn: ({ signal }) => api.workspaceFiles(signal),
  });
  const [filter, setFilter] = useState('all');
  const remove = useMutation({
    mutationFn: api.deleteArtifact,
    onSuccess: () => void client.invalidateQueries({ queryKey: ['artifacts'] }),
  });
  const visible = artifacts.data?.filter(
    (artifact) => filter === 'all' || artifact.format.toLowerCase() === filter,
  );
  return (
    <>
      <PageHeading
        eyebrow="MADE IN YOUR WORKSPACE"
        title="Your work, ready to take with you."
        description="Native Google files and downloadable reports, with their sources and verification details."
      />
      <h2>Google workspace files</h2>
      {workspaceFiles.isPending ? (
        <Spinner label="Loading Google files" />
      ) : workspaceFiles.isError ? (
        <ErrorNotice error={workspaceFiles.error} retry={() => void workspaceFiles.refetch()} />
      ) : workspaceFiles.data.length ? (
        <div className="artifact-library">
          {workspaceFiles.data.map((file) => (
            <WorkspaceFileCard key={file.id} file={file} />
          ))}
        </div>
      ) : (
        <p className="muted">
          Google Docs, Sheets, and Slides created or edited in this workspace will appear here.
        </p>
      )}
      <h2 className="settings-section">Downloadable files</h2>
      <div className="page-toolbar">
        <div className="filter-tabs" aria-label="Filter artifacts">
          {['all', 'pdf', 'docx', 'xlsx', 'pptx'].map((format) => (
            <button
              className={format === filter ? 'selected' : ''}
              key={format}
              aria-pressed={format === filter}
              onClick={() => setFilter(format)}
            >
              {format === 'all' ? 'All files' : format.toUpperCase()}
            </button>
          ))}
        </div>
        <span className="muted">{visible?.length ?? 0} files</span>
      </div>
      {remove.isError && <ErrorNotice error={remove.error} />}
      {artifacts.isPending ? (
        <Spinner label="Loading your files" />
      ) : artifacts.isError ? (
        <ErrorNotice error={artifacts.error} retry={() => void artifacts.refetch()} />
      ) : visible?.length ? (
        <div className="artifact-library">
          {visible.map((artifact) => (
            <ArtifactCard
              key={artifact.id}
              artifact={artifact}
              onDelete={() => {
                if (window.confirm(`Delete “${artifact.title}” from this workspace?`))
                  remove.mutate(artifact.id);
              }}
            />
          ))}
        </div>
      ) : (
        <Empty title="A clear space for your next deliverable">
          Ask the assistant to create a PDF brief, Word report, PowerPoint deck, or Excel tracker.
          Validated files will appear here.
        </Empty>
      )}
      <div className="page-footnote">
        <FileText size={15} />
        Downloads contain the actual generated format. File details describe structural readback
        validation.
      </div>
    </>
  );
}
