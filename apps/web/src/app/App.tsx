import { ChevronRight, Menu, ShieldCheck } from 'lucide-react';
import { Chat } from '../components/chat/Chat';
import { Brand } from '../components/layout/Brand';
import { Sidebar } from '../components/layout/Sidebar';
import { Chip } from '../components/ui/Chip';
import { ErrorNotice } from '../components/ui/ErrorNotice';
import { Spinner } from '../components/ui/Spinner';
import { SignIn } from '../features/authentication/SignIn';
import { useWorkspace } from '../hooks/useWorkspace';
import { ApprovalsPage } from './routes/ApprovalsPage';
import { ArtifactsPage } from './routes/ArtifactsPage';
import { ConnectorsPage } from './routes/ConnectorsPage';
import { ExplorerPage } from './routes/ExplorerPage';
import { pageNames } from './routes/navigation';
import { SettingsPage } from './routes/SettingsPage';

export default function App() {
  const {
    session,
    page,
    conversationId,
    menuOpen,
    setMenuOpen,
    narrow,
    navigationRef,
    online,
    user,
    conversations,
    connectors,
    approvals,
    pendingCount,
    logout,
    go,
    select,
  } = useWorkspace();
  if (session.isPending)
    return (
      <div className="app-loading">
        <Brand />
        <Spinner label="Opening your workspace" />
      </div>
    );
  if (session.isError)
    return (
      <div className="app-loading">
        <Brand />
        <ErrorNotice error={session.error} retry={() => void session.refetch()} />
      </div>
    );
  if (!user) return <SignIn session={session.data} />;
  const demo = ['mock', 'demo'].includes(session.data.mode);
  return (
    <div className="app-shell">
      <a
        className="skip-link"
        href="#main"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById('main')?.focus();
        }}
      >
        Skip to content
      </a>
      {menuOpen && (
        <button
          className="sidebar-overlay"
          onClick={() => setMenuOpen(false)}
          aria-label="Dismiss navigation overlay"
          tabIndex={-1}
        />
      )}
      <Sidebar
        {...{
          page,
          conversationId,
          menuOpen,
          setMenuOpen,
          narrow,
          navigationRef,
          user,
          conversations,
          connectors,
          pendingCount,
          logout,
          go,
          select,
          demo,
        }}
      />
      <div className="workspace-body" inert={narrow && menuOpen ? true : undefined}>
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="icon-button mobile-only"
              onClick={() => setMenuOpen(true)}
              aria-label="Open navigation"
              aria-expanded={menuOpen}
              aria-controls="workspace-navigation"
            >
              <Menu size={20} />
            </button>
            <span className="muted desktop-only">Workspace</span>
            <ChevronRight className="desktop-only" size={14} />
            <strong>{pageNames[page]}</strong>
          </div>
          <div className="topbar-status">
            {demo && (
              <Chip tone="demo">
                <span className="status-dot" />
                Synthetic demo data
              </Chip>
            )}
            <span className="model-status">
              <span className="status-dot" />
              {session.data.llm.model}
            </span>
          </div>
        </header>
        {!online && (
          <div className="offline-banner" role="status">
            You’re offline. Saved content remains visible; reconnect before sending a request.
          </div>
        )}
        <main id="main" className={page === 'chat' ? 'chat-main' : 'page-main'} tabIndex={-1}>
          {page === 'chat' && (
            <Chat
              key={conversationId ?? 'new'}
              conversationId={conversationId}
              onSelect={select}
              connectors={connectors.data ?? []}
              approvals={approvals.data ?? []}
              session={session.data}
              online={online}
            />
          )}
          {page === 'artifacts' && <ArtifactsPage />}
          {page === 'connectors' && <ConnectorsPage demo={demo} />}
          {page === 'mcp' && <ExplorerPage />}
          {page === 'approvals' && <ApprovalsPage />}
          {page === 'settings' && <SettingsPage session={session.data} />}
        </main>
        <footer className="workspace-footer">
          <span>
            <ShieldCheck size={12} />
            You control every external action.
          </span>
          <span>Built on Model Context Protocol</span>
        </footer>
      </div>
    </div>
  );
}
