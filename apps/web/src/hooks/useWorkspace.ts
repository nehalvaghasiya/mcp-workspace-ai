import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { currentPage, type Page } from '../app/routes/navigation';
import { api } from '../services/api';

export function useWorkspace() {
  const client = useQueryClient();
  const session = useQuery({
    queryKey: ['session'],
    queryFn: ({ signal }) => api.session(signal),
    retry: 1,
  });
  const [page, setPage] = useState<Page>(currentPage);
  const [conversationId, setConversationId] = useState<string>();
  const [menuOpen, setMenuOpen] = useState(false);
  const [narrow, setNarrow] = useState(() => window.matchMedia('(max-width: 760px)').matches);
  const navigationRef = useRef<HTMLElement>(null);
  const [online, setOnline] = useState(navigator.onLine);
  const [now, setNow] = useState(Date.now);
  const user = session.data?.user;
  const conversations = useQuery({
    queryKey: ['conversations'],
    queryFn: ({ signal }) => api.conversations(signal),
    enabled: !!user,
  });
  const connectors = useQuery({
    queryKey: ['connectors'],
    queryFn: ({ signal }) => api.connectors(signal),
    enabled: !!user,
  });
  const approvals = useQuery({
    queryKey: ['approvals'],
    queryFn: ({ signal }) => api.approvals(signal),
    enabled: !!user,
    refetchInterval: user ? 4000 : false,
  });
  const pendingCount =
    approvals.data?.filter((a) => a.status === 'pending' && Date.parse(a.expires_at) > now)
      .length ?? 0;
  const logout = useMutation({
    mutationFn: api.logout,
    onSuccess: () => {
      client.clear();
      setConversationId(undefined);
      void client.invalidateQueries({ queryKey: ['session'] });
    },
  });
  useEffect(() => {
    const changed = () => setPage(currentPage());
    const media = window.matchMedia('(max-width: 760px)');
    const resized = () => setNarrow(media.matches);
    media.addEventListener('change', resized);
    const connected = () => setOnline(true);
    const disconnected = () => setOnline(false);
    const shortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setConversationId(undefined);
        setPage('chat');
        setMenuOpen(false);
        window.location.hash = 'chat';
        requestAnimationFrame(() => document.getElementById('message-input')?.focus());
      }
    };
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    window.addEventListener('hashchange', changed);
    window.addEventListener('online', connected);
    window.addEventListener('offline', disconnected);
    window.addEventListener('keydown', shortcut);
    return () => {
      window.clearInterval(timer);
      media.removeEventListener('change', resized);
      window.removeEventListener('hashchange', changed);
      window.removeEventListener('online', connected);
      window.removeEventListener('offline', disconnected);
      window.removeEventListener('keydown', shortcut);
    };
  }, []);
  useEffect(() => {
    if (!menuOpen || !narrow) return;
    const panel = navigationRef.current;
    const controls = () =>
      Array.from(panel?.querySelectorAll<HTMLElement>('button:not(:disabled), a[href]') ?? []);
    controls()[0]?.focus();
    const keydown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMenuOpen(false);
        requestAnimationFrame(() =>
          document.querySelector<HTMLElement>('[aria-label="Open navigation"]')?.focus(),
        );
      }
      if (event.key === 'Tab') {
        const elements = controls();
        const first = elements[0];
        const last = elements.at(-1);
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    window.addEventListener('keydown', keydown);
    return () => window.removeEventListener('keydown', keydown);
  }, [menuOpen, narrow]);
  function go(next: Page) {
    setPage(next);
    window.location.hash = next;
    setMenuOpen(false);
    requestAnimationFrame(() => document.getElementById('main')?.focus());
  }
  function select(id?: string) {
    setConversationId(id);
    go('chat');
  }

  return {
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
  };
}
