import { type ToolTrace } from '@mcp-workspace/shared-types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api } from '../../services/api';
import { subscribeRun } from '../../services/run-events';
import { type ChatProps } from '../../types/chat-props';
import { type LiveRun } from '../../types/live-run';
import { isActiveRun } from '../workflows/run-state';

export function useConversation({
  conversationId,
  onSelect,
  approvals,
  online,
}: Pick<ChatProps, 'conversationId' | 'onSelect' | 'approvals' | 'online'>) {
  const client = useQueryClient();
  const [content, setContent] = useState('');
  const [timelineOpen, setTimelineOpen] = useState(
    () => window.matchMedia('(min-width: 1051px)').matches,
  );
  const [live, setLive] = useState<LiveRun>();
  const textarea = useRef<HTMLTextAreaElement>(null);
  const bottom = useRef<HTMLDivElement>(null);
  const submission = useRef<{ content: string; id: string; conversationId?: string }>(undefined);
  const conversation = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: ({ signal }) => api.conversation(conversationId!, signal),
    enabled: !!conversationId,
  });
  const lastRun = conversation.data?.runs?.at(-1);
  const runId = lastRun?.id;
  const runActive = isActiveRun(lastRun);
  const currentLive = live?.id === runId ? live : undefined;
  const active = isActiveRun(lastRun) && !currentLive?.finished;
  const trace = useQuery({
    queryKey: ['trace', runId],
    queryFn: ({ signal }) => api.trace(runId!, signal),
    enabled: !!runId,
    refetchInterval: active ? 1500 : false,
  });
  const refresh = () => {
    void client.invalidateQueries({ queryKey: ['conversation', conversationId] });
    void client.invalidateQueries({ queryKey: ['conversations'] });
    void client.invalidateQueries({ queryKey: ['approvals'] });
    void client.invalidateQueries({ queryKey: ['artifacts'] });
    void client.invalidateQueries({ queryKey: ['trace', runId] });
  };
  const send = useMutation({
    mutationFn: async (value: string) => {
      if (!submission.current || submission.current.content !== value) {
        submission.current = { content: value, id: crypto.randomUUID(), conversationId };
      }
      const pending = submission.current;
      pending.conversationId ??= (await api.createConversation()).id;
      const run = await api.send(pending.conversationId, value, pending.id);
      return run;
    },
    onSuccess: (run) => {
      setContent('');
      submission.current = undefined;
      if (!conversationId) onSelect(run.conversation_id);
      void client.invalidateQueries({ queryKey: ['conversation', run.conversation_id] });
      void client.invalidateQueries({ queryKey: ['conversations'] });
    },
    onError: () => textarea.current?.focus(),
  });
  const cancel = useMutation({ mutationFn: () => api.cancel(runId!), onSuccess: refresh });
  const deleteChat = useMutation({
    mutationFn: () => api.deleteConversation(conversationId!),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ['conversations'] });
      onSelect();
    },
  });
  useEffect(() => {
    if (!runId || !runActive) return;
    return subscribeRun(
      runId,
      (event) => {
        const terminal = ['run.completed', 'run.failed', 'run.cancelled'].includes(event.type);
        setLive((previous) => {
          const state =
            previous?.id === runId
              ? previous
              : { id: runId, text: '', events: [], finished: false, connected: true };
          return {
            ...state,
            events: [...state.events, event],
            text: event.type === 'message.delta' ? state.text + event.data.text : state.text,
            finished: terminal || state.finished,
            error:
              event.type === 'run.failed'
                ? `${event.data.message} (${event.data.code})`
                : state.error,
          };
        });
        if (terminal || event.type === 'approval.required') {
          void client.invalidateQueries({ queryKey: ['conversation', conversationId] });
          void client.invalidateQueries({ queryKey: ['approvals'] });
          void client.invalidateQueries({ queryKey: ['artifacts'] });
          void client.invalidateQueries({ queryKey: ['trace', runId] });
          void client.invalidateQueries({ queryKey: ['conversations'] });
        }
      },
      (connected) =>
        setLive((previous) => ({
          ...(previous?.id === runId
            ? previous
            : { id: runId, text: '', events: [], finished: false }),
          connected,
        })),
    );
  }, [runId, runActive, conversationId, client]);
  useEffect(() => {
    bottom.current?.scrollIntoView({ block: 'end', behavior: 'auto' });
  }, [conversation.data?.messages.length, currentLive?.text]);
  const runApprovals = approvals.filter(
    (approval) => approval.run_id === runId && approval.status === 'pending',
  );
  const tools =
    currentLive?.events.filter(
      (event) => event.type === 'tool.started' || event.type === 'tool.completed',
    ) ?? [];
  const streamedTrace: ToolTrace[] = [];
  for (const event of tools) {
    if (event.type === 'tool.started')
      streamedTrace.push({ ...event.data, status: 'running', id: String(event.id) });
    else if (event.type === 'tool.completed') {
      const pending = [...streamedTrace]
        .reverse()
        .find((t) => t.tool === event.data.tool && t.status === 'running');
      const status = event.data.status === 'error' ? 'failed' : 'completed';
      const result = {
        ...event.data,
        status,
        error: status === 'failed' ? (event.data.code ?? 'Tool failed') : undefined,
      };
      if (pending) Object.assign(pending, result);
      else streamedTrace.push({ ...result, id: String(event.id) });
    }
  }
  const timeline = streamedTrace.length ? streamedTrace : (trace.data ?? []);
  const messages = conversation.data?.messages ?? [];
  const hasMessages = messages.length > 0;
  function submit(event: FormEvent) {
    event.preventDefault();
    if (content.trim() && !active && !send.isPending && online) send.mutate(content.trim());
  }

  return {
    content,
    setContent,
    timelineOpen,
    setTimelineOpen,
    textarea,
    bottom,
    conversation,
    lastRun,
    runId,
    currentLive,
    active,
    trace,
    refresh,
    send,
    cancel,
    deleteChat,
    runApprovals,
    timeline,
    messages,
    hasMessages,
    submit,
  };
}
