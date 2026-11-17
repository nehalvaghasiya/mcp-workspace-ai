import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { ArtifactCard } from '../../src/components/artifacts/ArtifactCard';
import { SafeMarkdown } from '../../src/components/ui/SafeMarkdown';
import { Sources } from '../../src/components/chat/Sources';
import { WorkspaceFileCard } from '../../src/components/artifacts/WorkspaceFileCard';

it('labels a synthetic source with no provider link truthfully', () => {
  render(
    <Sources
      sources={[
        {
          provider: 'gmail',
          resource_id: 'mock-mail-001',
          title: 'Launch recap',
          url: null,
          retrieved_at: '2026-11-05T12:00:00Z',
          pointer: '',
          snippet: '<script>untrusted content</script>',
        },
      ]}
    />,
  );
  expect(screen.getByText('Synthetic demo source · no external link')).toBeInTheDocument();
  expect(screen.queryByRole('link')).not.toBeInTheDocument();
  expect(document.querySelector('script')).toBeNull();
});
it('renders model Markdown without external images or active HTML', () => {
  render(
    <SafeMarkdown>
      {
        '![Tracking image](https://tracker.example.invalid/open)\n\n<script>alert(1)</script>\n\n[Unsafe](javascript:alert(1))'
      }
    </SafeMarkdown>,
  );
  expect(document.querySelector('img')).toBeNull();
  expect(document.querySelector('script')).toBeNull();
  expect(screen.queryByRole('link')).not.toBeInTheDocument();
  expect(screen.getByText('[Image: Tracking image]')).toBeInTheDocument();
});
it('shows validation accurately and uses the authenticated artifact endpoint', () => {
  render(
    <ArtifactCard
      artifact={{
        id: 'owned',
        title: 'brief.pdf',
        format: 'pdf',
        mime_type: 'application/pdf',
        size: 2048,
        sha256: 'abcdef',
        created_at: '2026-11-05T12:00:00Z',
        validated: false,
        download_url: '/api/artifacts/owned/download',
        sources: [],
      }}
    />,
  );
  expect(screen.getByText('Validation unavailable')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Download brief.pdf' })).toHaveAttribute(
    'href',
    '/api/artifacts/owned/download',
  );
});
it('links native files to Google and discloses partial creation', () => {
  render(
    <WorkspaceFileCard
      file={{
        id: 'owned-native',
        google_file_id: 'doc-123',
        kind: 'docs',
        title: 'Live report',
        mime_type: 'application/vnd.google-apps.document',
        web_url: 'https://docs.google.com/document/d/doc-123/edit',
        revision: '',
        status: 'partial',
        artifact_id: null,
        run_id: null,
        created_at: '2026-11-05T12:00:00Z',
        updated_at: '2026-11-05T12:00:00Z',
      }}
    />,
  );
  expect(screen.getByRole('link', { name: 'Open Live report in Google' })).toHaveAttribute(
    'href',
    'https://docs.google.com/document/d/doc-123/edit',
  );
  expect(screen.getByText('Partially created · review in Google')).toBeInTheDocument();
  expect(screen.queryByText('Google readback verified')).not.toBeInTheDocument();
});
