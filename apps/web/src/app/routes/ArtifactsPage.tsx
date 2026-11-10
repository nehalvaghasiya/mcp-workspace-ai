import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { FileText } from 'lucide-react';
import { useState } from 'react';
import { ArtifactCard } from '../../components/artifacts/ArtifactCard';
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
        description="Generated files, their sources, and the details that make them verifiable."
      />
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
