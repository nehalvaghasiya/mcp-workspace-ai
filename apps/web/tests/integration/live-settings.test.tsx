import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, expect, it, vi } from 'vitest';
import type { Connector, Session, Settings } from '@mcp-workspace/shared-types';
import { SettingsForm } from '../../src/features/settings/SettingsForm';
import { ConnectorsPage } from '../../src/app/routes/ConnectorsPage';
import { api } from '../../src/services/api';

afterEach(() => vi.restoreAllMocks());

it('saving preferences invalidates settings without replacing them with mutation status', async () => {
  const settings: Settings = {
    provider: 'openai_compatible',
    provider_url: 'https://model.example.invalid/v1',
    model: 'configured-model',
    timezone: 'America/Chicago',
    llm_consent: false,
  };
  const session: Session = {
    mode: 'live',
    user: {
      id: 'owner',
      display_name: 'Owner',
      email: 'owner@example.invalid',
      timezone: 'America/Chicago',
    },
    csrf_token: 'synthetic-csrf',
    llm: { provider: 'openai_compatible', model: 'configured-model', consented: false },
  };
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  client.setQueryData(['settings'], settings);
  vi.spyOn(api, 'updateSettings').mockResolvedValue({ status: 'saved' });
  render(
    <QueryClientProvider client={client}>
      <SettingsForm settings={settings} session={session} />
    </QueryClientProvider>,
  );
  await userEvent.click(screen.getByRole('button', { name: 'Save preferences' }));
  await waitFor(() => expect(screen.getByText('Preferences saved')).toBeInTheDocument());
  expect(client.getQueryData(['settings'])).toEqual(settings);
  expect(client.getQueryState(['settings'])?.isInvalidated).toBe(true);
  expect(screen.getByText('configured-model')).toBeInTheDocument();
  expect(
    screen.getByText('Model processing is paused until you allow it and save your preferences.'),
  ).toBeInTheDocument();
});

it('offers real OAuth permissions for all six services and reports missing access honestly', async () => {
  const connectors: Connector[] = ['gmail', 'calendar', 'drive', 'docs', 'sheets', 'slides'].map(
    (id) => ({
      id,
      name: id,
      enabled: true,
      mode: 'live',
      status: 'needs_permission',
      scopes: [],
      available_capabilities: [],
      missing_scopes: ['synthetic-scope'],
      last_error: null,
    }),
  );
  vi.spyOn(api, 'connectors').mockResolvedValue(connectors);
  render(
    <QueryClientProvider client={new QueryClient()}>
      <ConnectorsPage demo={false} />
    </QueryClientProvider>,
  );
  await screen.findByRole('heading', { name: 'slides' });
  expect(screen.getAllByText('Permission needed')).toHaveLength(6);
  const links = screen.getAllByRole('link');
  for (const id of ['gmail', 'calendar', 'drive', 'docs', 'sheets', 'slides']) {
    expect(
      links.some(
        (link) =>
          link.getAttribute('href') === `/api/auth/google/start?connector=${id}&access=read`,
      ),
    ).toBe(true);
    expect(
      links.some(
        (link) =>
          link.getAttribute('href') === `/api/auth/google/start?connector=${id}&access=write`,
      ),
    ).toBe(true);
  }
  expect(screen.queryByText('Connected', { exact: true })).not.toBeInTheDocument();
});
