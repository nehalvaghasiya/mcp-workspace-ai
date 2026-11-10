import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, expect, it, vi } from 'vitest';
import type { Approval } from '@mcp-workspace/shared-types';
import { api } from '../../src/services/api';
import { ApprovalCard } from '../../src/components/approvals/ApprovalCard';

const approval: Approval = {
  id: 'approval-1',
  run_id: 'run-1',
  tool: 'gmail.send_draft',
  arguments: {
    to: ['alex@example.invalid'],
    subject: 'Launch decision',
    body_text: 'Confirming the reviewed launch timeline.',
    attachments: [],
  },
  summary: 'Send launch decision to Alex',
  status: 'pending',
  expires_at: '2099-11-05T22:00:00Z',
  action_digest: 'exact-action-sha256',
};
afterEach(() => vi.restoreAllMocks());
function show(value: Approval) {
  return render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { mutations: { retry: false } } })}
    >
      <ApprovalCard approval={value} />
    </QueryClientProvider>,
  );
}

it('shows exact recipients and content, submits one decision, then disables replay', async () => {
  const decide = vi.spyOn(api, 'decide').mockResolvedValue({ status: 'consumed' });
  show(approval);
  expect(screen.getByText(/alex@example.invalid/)).toBeInTheDocument();
  expect(screen.getByText('Confirming the reviewed launch timeline.')).toBeInTheDocument();
  const button = screen.getByRole('button', { name: 'Approve exact action' });
  await userEvent.click(button);
  await waitFor(() => expect(button).toBeDisabled());
  expect(decide).toHaveBeenCalledExactlyOnceWith('approval-1', 'approve');
  expect(screen.getByText('consumed')).toBeInTheDocument();
  await userEvent.click(button);
  expect(decide).toHaveBeenCalledTimes(1);
});
it('disables expired approvals without allowing a decision', () => {
  const decide = vi.spyOn(api, 'decide');
  show({ ...approval, expires_at: '2000-01-01T00:00:00Z' });
  expect(screen.getByRole('button', { name: 'Approve exact action' })).toBeDisabled();
  expect(screen.getByRole('button', { name: 'Reject' })).toBeDisabled();
  expect(screen.getByText('Expired')).toBeInTheDocument();
  expect(decide).not.toHaveBeenCalled();
});
it('shows the exact snapshot when a send action only carries a draft identifier', () => {
  show({
    ...approval,
    summary: {
      to: ['alex@example.invalid'],
      subject: 'Exact saved draft',
      body_text: 'The exact draft text to send.',
    },
    arguments: { draft_id: 'draft-123' },
  });
  expect(screen.getByRole('heading', { name: 'Send this email' })).toBeInTheDocument();
  expect(screen.getByText('The exact draft text to send.')).toBeInTheDocument();
  expect(screen.getByText('draft-123')).toBeInTheDocument();
  expect(screen.getByText(/alex@example.invalid/)).toBeInTheDocument();
});
it('shows a server rejection and leaves the exact action available for refresh', async () => {
  vi.spyOn(api, 'decide').mockRejectedValue(
    new Error('Action digest changed; request a fresh approval.'),
  );
  show(approval);
  await userEvent.click(screen.getByRole('button', { name: 'Approve exact action' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Action digest changed');
});
