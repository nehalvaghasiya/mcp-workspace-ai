import ReactMarkdown from 'react-markdown';
import { safeSourceUrl } from '../../lib/urls';

export function SafeMarkdown({ children }: { children: string }) {
  return (
    <ReactMarkdown
      components={{
        img: ({ alt }) => <span className="muted">[Image: {alt || 'not loaded'}]</span>,
        a: ({ href, children: label }) => {
          const url = safeSourceUrl(href ?? null);
          return url ? (
            <a href={url} target="_blank" rel="noopener noreferrer">
              {label}
            </a>
          ) : (
            <span>{label}</span>
          );
        },
      }}
    >
      {children}
    </ReactMarkdown>
  );
}
