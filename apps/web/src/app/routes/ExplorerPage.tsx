import { useQuery } from '@tanstack/react-query';
import { Boxes, ChevronRight, Search, ShieldCheck } from 'lucide-react';
import { useState } from 'react';
import { PageHeading } from '../../components/layout/PageHeading';
import { Chip } from '../../components/ui/Chip';
import { Empty } from '../../components/ui/Empty';
import { ErrorNotice } from '../../components/ui/ErrorNotice';
import { JsonBlock } from '../../components/ui/JsonBlock';
import { Spinner } from '../../components/ui/Spinner';
import { api } from '../../services/api';

export function ExplorerPage() {
  const servers = useQuery({ queryKey: ['servers'], queryFn: ({ signal }) => api.servers(signal) });
  const tools = useQuery({ queryKey: ['tools'], queryFn: ({ signal }) => api.tools(signal) });
  const [serverId, setServerId] = useState('all');
  const [search, setSearch] = useState('');
  const visible = tools.data?.filter(
    (tool) =>
      (serverId === 'all' || tool.server === serverId) &&
      tool.name.toLowerCase().includes(search.toLowerCase()),
  );
  return (
    <>
      <PageHeading
        eyebrow="MODEL CONTEXT PROTOCOL"
        title="See how your workspace connects."
        description="Inspect the server registry, negotiated protocol, tool schemas, and enforced risk classifications."
      />
      {servers.isError && (
        <ErrorNotice error={servers.error} retry={() => void servers.refetch()} />
      )}
      <div className="explorer-layout">
        <aside className="server-list" aria-label="MCP servers">
          <button
            className={serverId === 'all' ? 'selected' : ''}
            onClick={() => setServerId('all')}
          >
            <Boxes size={18} />
            <span>
              All servers<small>{servers.data?.length ?? 0} registered</small>
            </span>
            <ChevronRight size={14} />
          </button>
          {servers.isPending ? (
            <Spinner label="Discovering servers" />
          ) : (
            servers.data?.map((server) => (
              <button
                key={server.id}
                className={serverId === server.id ? 'selected' : ''}
                onClick={() => setServerId(server.id)}
              >
                <span
                  className={`status-dot ${['healthy', 'connected', 'ready', 'online'].includes(server.status) ? '' : 'disabled'}`}
                />
                <span>
                  {server.name}
                  <small>
                    {server.transport} · {server.status}
                  </small>
                  <code>{server.protocol_version}</code>
                </span>
                <ChevronRight size={14} />
              </button>
            ))
          )}
        </aside>
        <section className="tool-catalog" aria-label="Tool catalog">
          <div className="catalog-toolbar">
            <h2>
              Tools <span>{visible?.length ?? 0}</span>
            </h2>
            <label className="search-field">
              <Search size={16} />
              <input
                aria-label="Search tools"
                type="search"
                placeholder="Search tools…"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </label>
          </div>
          {tools.isPending ? (
            <Spinner label="Loading tool schemas" />
          ) : tools.isError ? (
            <ErrorNotice error={tools.error} retry={() => void tools.refetch()} />
          ) : visible?.length ? (
            <div className="tool-list">
              {visible.map((tool) => (
                <details className="catalog-tool" key={`${tool.server}:${tool.name}`}>
                  <summary>
                    <span className="catalog-tool-icon">
                      <Boxes size={16} />
                    </span>
                    <div>
                      <strong>{tool.name}</strong>
                      <span>{tool.server}</span>
                    </div>
                    <Chip tone={tool.risk === 'READ' ? 'positive' : 'warning'}>
                      {tool.risk.replaceAll('_', ' ')}
                    </Chip>
                    <Chip>{tool.enabled ? 'Enabled' : 'Disabled'}</Chip>
                  </summary>
                  <div className="catalog-tool-content">
                    <p className="eyebrow">INPUT SCHEMA</p>
                    <JsonBlock value={tool.input_schema} />
                    {tool.output_schema != null && (
                      <>
                        <p className="eyebrow">OUTPUT SCHEMA</p>
                        <JsonBlock value={tool.output_schema} />
                      </>
                    )}
                    <dl>
                      <dt>Schema digest</dt>
                      <dd className="hash">{tool.digest}</dd>
                    </dl>
                  </div>
                </details>
              ))}
            </div>
          ) : (
            <Empty title="No matching tools">Try another name or select a different server.</Empty>
          )}
        </section>
      </div>
      <div className="page-footnote">
        <ShieldCheck size={15} />
        This registry is configured by the operator. Tool schemas are inspectable data and cannot
        override approval policy.
      </div>
    </>
  );
}
