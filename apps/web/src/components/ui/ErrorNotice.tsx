import { AlertCircle } from 'lucide-react';

export function ErrorNotice({ error, retry }: { error: unknown; retry?: () => void }) {
  return (
    <div className="error-notice" role="alert">
      <AlertCircle size={18} aria-hidden="true" />
      <div>
        <p>{error instanceof Error ? error.message : 'Something went wrong. Please try again.'}</p>
        {retry && (
          <button className="text-button" onClick={retry}>
            Try again
          </button>
        )}
      </div>
    </div>
  );
}
