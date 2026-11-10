import { type User } from '@mcp-workspace/shared-types';
import { ChevronRight, History, LogOut, MessageSquare, Plus, Settings2, X } from 'lucide-react';
import { navigation } from '../../app/routes/navigation';
import { useWorkspace } from '../../hooks/useWorkspace';
import { ErrorNotice } from '../ui/ErrorNotice';
import { Spinner } from '../ui/Spinner';
import { Brand } from './Brand';

type SidebarProps = Pick<
  ReturnType<typeof useWorkspace>,
  | 'page'
  | 'conversationId'
  | 'menuOpen'
  | 'setMenuOpen'
  | 'narrow'
  | 'navigationRef'
  | 'conversations'
  | 'connectors'
  | 'pendingCount'
  | 'logout'
  | 'go'
  | 'select'
> & { user: User; demo: boolean };

export function Sidebar({
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
}: SidebarProps) {
  return (
    <aside
      id="workspace-navigation"
      ref={navigationRef}
      className={`sidebar ${menuOpen ? 'open' : ''}`}
      aria-label="Workspace navigation"
      role={narrow && menuOpen ? 'dialog' : undefined}
      aria-modal={narrow && menuOpen ? true : undefined}
      inert={narrow && !menuOpen ? true : undefined}
    >
      <div className="sidebar-brand">
        <Brand />
        <button
          className="icon-button mobile-only"
          aria-label="Close navigation"
          onClick={() => setMenuOpen(false)}
        >
          <X size={20} />
        </button>
      </div>
      <button className="new-chat button" onClick={() => select()}>
        <Plus size={17} />
        New conversation<span>⌘ K</span>
      </button>
      <nav>
        {navigation.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => go(id)}
            className={`nav-item ${page === id ? 'active' : ''}`}
            aria-current={page === id ? 'page' : undefined}
          >
            <Icon size={18} />
            <span>{label}</span>
            {id === 'approvals' && pendingCount > 0 && (
              <span className="count">{pendingCount}</span>
            )}
            {page === id && <span className="nav-active-mark" />}
          </button>
        ))}
      </nav>
      <div className="history-heading">
        <span>
          <History size={14} />
          Recent conversations
        </span>
      </div>
      <div className="conversation-list">
        {conversations.isPending ? (
          <Spinner />
        ) : conversations.isError ? (
          <ErrorNotice error={conversations.error} retry={() => void conversations.refetch()} />
        ) : conversations.data?.length ? (
          conversations.data.map((conversation) => (
            <button
              className={`history-item ${conversationId === conversation.id && page === 'chat' ? 'selected' : ''}`}
              key={conversation.id}
              onClick={() => select(conversation.id)}
              title={conversation.title}
            >
              <MessageSquare size={14} />
              <span>{conversation.title}</span>
            </button>
          ))
        ) : (
          <p className="history-empty">Your conversations will appear here.</p>
        )}
      </div>
      <div className="sidebar-bottom">
        <div className="connection-summary">
          <span className="status-dot" />
          <span>{connectors.data?.filter((c) => c.enabled).length ?? 0} connectors enabled</span>
          <button
            className="icon-button"
            aria-label="Manage connectors"
            onClick={() => go('connectors')}
          >
            <ChevronRight size={15} />
          </button>
        </div>
        <button
          className={`nav-item ${page === 'settings' ? 'active' : ''}`}
          onClick={() => go('settings')}
        >
          <Settings2 size={18} />
          Settings
        </button>
        <div className="user-row">
          <span className="avatar">{user.display_name.slice(0, 1).toUpperCase()}</span>
          <div>
            <strong>{user.display_name}</strong>
            <span>{demo ? 'Synthetic demo account' : (user.email ?? 'Connected account')}</span>
          </div>
          <button
            className="icon-button"
            onClick={() => logout.mutate()}
            aria-label="Sign out"
            disabled={logout.isPending}
          >
            <LogOut size={17} />
          </button>
        </div>
        {logout.isError && <ErrorNotice error={logout.error} />}
      </div>
    </aside>
  );
}
