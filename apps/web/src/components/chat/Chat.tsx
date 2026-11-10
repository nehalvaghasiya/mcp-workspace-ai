import {
  ArrowUp,
  Command,
  PanelRightClose,
  PanelRightOpen,
  Sparkles,
  Square,
  Trash2,
} from 'lucide-react';
import { useConversation } from '../../features/conversations/useConversation';
import { type ChatProps } from '../../types/chat-props';
import { ApprovalCard } from '../approvals/ApprovalCard';
import { ArtifactCard } from '../artifacts/ArtifactCard';
import { ErrorNotice } from '../ui/ErrorNotice';
import { SafeMarkdown } from '../ui/SafeMarkdown';
import { Spinner } from '../ui/Spinner';
import { ActivityPanel } from './ActivityPanel';
import { Sources } from './Sources';
import { Welcome } from './Welcome';

export function Chat({
  conversationId,
  onSelect,
  connectors,
  approvals,
  session,
  online,
}: ChatProps) {
  const {
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
  } = useConversation({ conversationId, onSelect, approvals, online });
  return (
    <div className={`chat-layout ${timelineOpen ? 'with-timeline' : ''}`}>
      <section className="chat-column" aria-label="Conversation">
        {hasMessages && (
          <div className="conversation-header">
            <div>
              <span className="eyebrow">CONVERSATION</span>
              <h1>{conversation.data?.title}</h1>
            </div>
            <div className="inline-actions">
              <button
                className="icon-button"
                aria-label="Delete conversation"
                onClick={() => {
                  if (window.confirm('Delete this conversation and its local history?'))
                    deleteChat.mutate();
                }}
                disabled={active || deleteChat.isPending}
              >
                <Trash2 size={17} />
              </button>
              <button
                className="icon-button"
                aria-label={timelineOpen ? 'Hide activity' : 'Show activity'}
                onClick={() => setTimelineOpen(!timelineOpen)}
              >
                {timelineOpen ? <PanelRightClose size={18} /> : <PanelRightOpen size={18} />}
              </button>
            </div>
          </div>
        )}
        <div className="chat-scroll">
          {conversation.isPending && conversationId ? (
            <div className="conversation-loading">
              <Spinner label="Loading conversation" />
            </div>
          ) : conversation.isError ? (
            <ErrorNotice error={conversation.error} retry={() => void conversation.refetch()} />
          ) : !hasMessages ? (
            <Welcome
              connectors={connectors}
              onPrompt={(text) => {
                setContent(text);
                textarea.current?.focus();
              }}
            />
          ) : (
            <div className="messages">
              {messages.map((message) => (
                <article key={message.id} className={`message ${message.role}`}>
                  <div className="message-avatar">
                    {message.role === 'user' ? (
                      session.user?.display_name.slice(0, 1)
                    ) : (
                      <Command size={17} />
                    )}
                  </div>
                  <div className="message-content">
                    <div className="message-label">
                      {message.role === 'user' ? 'You' : 'Workspace AI'}
                      <span>{message.id.slice(0, 8)}</span>
                    </div>
                    <div className="prose">
                      <SafeMarkdown>{message.content}</SafeMarkdown>
                    </div>
                    <Sources sources={message.sources ?? []} />
                    {!!message.artifacts?.length && (
                      <div className="message-artifacts">
                        {message.artifacts.map((artifact) => (
                          <ArtifactCard key={artifact.id} artifact={artifact} />
                        ))}
                      </div>
                    )}
                  </div>
                </article>
              ))}
              {active && (
                <article className="message assistant streaming">
                  <div className="message-avatar">
                    <Command size={17} />
                  </div>
                  <div className="message-content">
                    <div className="message-label">Workspace AI</div>
                    {currentLive?.text ? (
                      <div className="prose">
                        <SafeMarkdown>{currentLive.text}</SafeMarkdown>
                      </div>
                    ) : (
                      <Spinner
                        label={
                          runApprovals.length
                            ? 'Waiting for your decision'
                            : 'Working through your request'
                        }
                      />
                    )}
                  </div>
                </article>
              )}
              {currentLive?.error && (
                <ErrorNotice error={new Error(currentLive.error)} retry={refresh} />
              )}
              {lastRun?.status === 'cancelled' && (
                <p className="run-notice">
                  Run cancelled. Completed tool actions remain recorded in activity.
                </p>
              )}
              {['failed', 'interrupted'].includes(lastRun?.status ?? '') && !currentLive?.error && (
                <ErrorNotice
                  error={
                    new Error(
                      'This run stopped before completing. Inspect the activity for completed actions before trying a new request.',
                    )
                  }
                  retry={refresh}
                />
              )}
              {runApprovals.map((approval) => (
                <ApprovalCard key={approval.id} approval={approval} onDecision={refresh} />
              ))}
              <div ref={bottom} />
            </div>
          )}
        </div>
        <div className="composer-region">
          {send.isError && (
            <>
              <ErrorNotice error={send.error} />
              <p className="run-notice">
                The request could not be confirmed. Retrying the same text uses the same request ID;
                completed actions remain recorded in history.
              </p>
            </>
          )}
          {cancel.isError && <ErrorNotice error={cancel.error} />}
          {deleteChat.isError && <ErrorNotice error={deleteChat.error} />}
          {active && currentLive?.connected === false && (
            <div className="connection-warning" role="status">
              Activity connection interrupted. Reconnecting to saved events…
            </div>
          )}
          <form className="composer" onSubmit={submit}>
            <label className="sr-only" htmlFor="message-input">
              Message Workspace AI
            </label>
            <textarea
              id="message-input"
              ref={textarea}
              value={content}
              onChange={(event) => setContent(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
              placeholder="Ask something, or make something…"
              rows={2}
              maxLength={12000}
              disabled={send.isPending}
            />
            <div className="composer-toolbar">
              <div>
                <span className="composer-model">
                  <Sparkles size={13} />
                  {session.llm.model}
                </span>
                <span className="composer-context">
                  {connectors.filter((c) => c.enabled).length} connectors
                </span>
              </div>
              {active ? (
                <button
                  type="button"
                  className="send-button cancel"
                  aria-label="Cancel run"
                  onClick={() => cancel.mutate()}
                  disabled={cancel.isPending}
                >
                  <Square size={15} fill="currentColor" />
                </button>
              ) : (
                <button
                  type="submit"
                  className="send-button"
                  aria-label="Send message"
                  disabled={!content.trim() || send.isPending || !online}
                >
                  {send.isPending ? <Spinner label="" /> : <ArrowUp size={19} />}
                </button>
              )}
            </div>
          </form>
          <p className="composer-note">
            AI can make mistakes. Check the sources. <span>↵ send · Shift ↵ new line</span>
          </p>
        </div>
      </section>
      {timelineOpen && (
        <ActivityPanel
          {...{ hasMessages, runId, active, currentLive, lastRun, timeline, trace }}
          onClose={() => setTimelineOpen(false)}
        />
      )}
      {!timelineOpen && (
        <button className="show-activity button" onClick={() => setTimelineOpen(true)}>
          <PanelRightOpen size={15} />
          Activity
        </button>
      )}
    </div>
  );
}
