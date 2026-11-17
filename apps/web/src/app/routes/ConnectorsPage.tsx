import { type Connector } from '@mcp-workspace/shared-types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Check, ExternalLink, Plug, ShieldCheck } from 'lucide-react';
import { CalendarIcon } from '../../components/connections/CalendarIcon';
import { DriveIcon } from '../../components/connections/DriveIcon';
import { MailIcon } from '../../components/connections/MailIcon';
import { PageHeading } from '../../components/layout/PageHeading';
import { Chip } from '../../components/ui/Chip';
import { ErrorNotice } from '../../components/ui/ErrorNotice';
import { Spinner } from '../../components/ui/Spinner';
import { connectorDetails, connectorStatus } from '../../features/authentication/connector-details';
import { api } from '../../services/api';

export function ConnectorsPage({ demo }: { demo: boolean }) {
  const client = useQueryClient();
  const connectors = useQuery({
    queryKey: ['connectors'],
    queryFn: ({ signal }) => api.connectors(signal),
  });
  const toggle = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      api.toggleConnector(id, enabled),
    onMutate: async ({ id, enabled }) => {
      await client.cancelQueries({ queryKey: ['connectors'] });
      const previous = client.getQueryData<Connector[]>(['connectors']);
      client.setQueryData<Connector[]>(['connectors'], (items) =>
        items?.map((item) => (item.id === id ? { ...item, enabled } : item)),
      );
      return { previous };
    },
    onError: (_error, _variables, context) => {
      if (context?.previous) client.setQueryData(['connectors'], context.previous);
    },
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ['connectors'] });
      void client.invalidateQueries({ queryKey: ['tools'] });
    },
  });
  const disconnect = useMutation({
    mutationFn: api.disconnect,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ['connectors'] });
      void client.invalidateQueries({ queryKey: ['tools'] });
    },
  });
  return (
    <>
      <PageHeading
        eyebrow="YOUR CONNECTED WORKSPACE"
        title="The right context, within reach."
        description="Choose which tools the assistant can use. You stay in control of access and external actions."
      />
      {demo && (
        <div className="info-banner">
          <ShieldCheck size={18} />
          <div>
            <strong>Demo data is active.</strong>
            <p>
              These connectors use synthetic sample records. No real Google account is connected.
            </p>
          </div>
        </div>
      )}
      {connectors.isPending ? (
        <Spinner label="Checking connectors" />
      ) : connectors.isError ? (
        <ErrorNotice error={connectors.error} retry={() => void connectors.refetch()} />
      ) : (
        <div className="connector-grid">
          {connectors.data.map((connector) => (
            <article className="connector-card" key={connector.id}>
              <div className="connector-card-heading">
                <span className="connector-logo">
                  {connector.id === 'gmail' ? (
                    <MailIcon />
                  ) : connector.id === 'calendar' ? (
                    <CalendarIcon />
                  ) : connector.id === 'drive' ? (
                    <DriveIcon />
                  ) : (
                    <Plug size={26} />
                  )}
                </span>
                <Chip
                  tone={
                    connector.enabled && ['connected', 'mock'].includes(connector.status)
                      ? 'positive'
                      : ''
                  }
                >
                  {connectorStatus[connector.status] ?? connector.status.replaceAll('_', ' ')}
                </Chip>
              </div>
              <h2>{connector.name}</h2>
              <p>
                {connectorDetails[connector.id]?.description ?? 'Use authorized workspace content.'}
              </p>
              <div className="connector-mode">
                <span className={`status-dot ${connector.enabled ? '' : 'disabled'}`} />
                {['mock', 'demo'].includes(connector.mode)
                  ? 'Demo data · synthetic'
                  : 'Google connector · live'}
              </div>
              {!!connector.available_capabilities?.length && (
                <p className="muted">
                  Available: {connector.available_capabilities.join(', ').replaceAll('_', ' ')}
                </p>
              )}
              {!!connector.missing_scopes?.length && (
                <p className="muted">
                  Additional permission is needed for some actions. Review access below.
                </p>
              )}
              {connector.last_error && <p role="status">{connector.last_error}</p>}
              <details>
                <summary>
                  Granted scopes <span>{connector.scopes.length}</span>
                </summary>
                {connector.scopes.length ? (
                  <ul className="scope-list">
                    {connector.scopes.map((scope) => (
                      <li key={scope}>
                        <Check size={13} />
                        <code>{scope}</code>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">No scopes granted.</p>
                )}
              </details>
              <div className="connector-controls">
                <label className="switch-label">
                  <input
                    type="checkbox"
                    role="switch"
                    checked={connector.enabled}
                    disabled={
                      toggle.isPending ||
                      (!demo &&
                        ['disconnected', 'not_connected', 'expired'].includes(connector.status))
                    }
                    onChange={(event) =>
                      toggle.mutate({ id: connector.id, enabled: event.target.checked })
                    }
                    aria-label={`Enable ${connector.name}`}
                  />
                  <span className="switch-track" />
                  <span>{connector.enabled ? 'Enabled' : 'Disabled'}</span>
                </label>
                {!demo && connectorDetails[connector.id] && (
                  <a
                    className="text-button"
                    href={`/api/auth/google/start?connector=${encodeURIComponent(connector.id)}&access=read`}
                  >
                    {connector.status === 'connected' ? 'Review access' : 'Connect'}
                    <ExternalLink size={13} />
                  </a>
                )}
              </div>
              {!demo && connectorDetails[connector.id] && (
                <a
                  className="connector-write-access text-button"
                  href={`/api/auth/google/start?connector=${encodeURIComponent(connector.id)}&access=write`}
                >
                  {connectorDetails[connector.id]?.writeLabel}
                  <ExternalLink size={12} />
                </a>
              )}
            </article>
          ))}
        </div>
      )}
      {toggle.isError && <ErrorNotice error={toggle.error} />}
      {!demo && (
        <div className="settings-section">
          <h2>Disconnect Google</h2>
          <p>
            Revoke the Google grant for all connected services and remove stored credentials. This
            does not delete your Google files or messages.
          </p>
          <button
            className="button danger"
            onClick={() => {
              if (window.confirm('Disconnect all Google connectors and revoke this app’s grant?'))
                disconnect.mutate();
            }}
            disabled={disconnect.isPending}
          >
            Disconnect all Google access
          </button>
          {disconnect.isError && <ErrorNotice error={disconnect.error} />}
        </div>
      )}
      <div className="page-footnote">
        <ShieldCheck size={15} />
        Disabled connectors cannot be used by the assistant. Access tokens stay on the server.
      </div>
    </>
  );
}
