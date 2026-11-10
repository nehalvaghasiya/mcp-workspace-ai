import { type Session } from '@mcp-workspace/shared-types';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowRight, FileText, ShieldCheck } from 'lucide-react';
import { CalendarIcon } from '../../components/connections/CalendarIcon';
import { DriveIcon } from '../../components/connections/DriveIcon';
import { MailIcon } from '../../components/connections/MailIcon';
import { Brand } from '../../components/layout/Brand';
import { ErrorNotice } from '../../components/ui/ErrorNotice';
import { Spinner } from '../../components/ui/Spinner';
import { api } from '../../services/api';

export function SignIn({ session }: { session: Session }) {
  const client = useQueryClient();
  const demo = useMutation({
    mutationFn: api.demo,
    onSuccess: (value) => {
      client.setQueryData(['session'], value);
    },
  });
  const mockAvailable = ['mock', 'demo'].includes(session.mode);
  return (
    <main className="signin">
      <Brand />
      <div className="signin-content">
        <div className="eyebrow">
          <span className="status-dot" />
          ONE CHAT. CONNECTED TO YOUR WORK.
        </div>
        <h1>
          A little more clarity.
          <br />A lot less busywork.
        </h1>
        <p>
          Bring your messages, meetings, and documents into one workspace—with sources you can
          inspect and actions you control.
        </p>
        <div className="signin-integrations">
          <span>
            <MailIcon />
            Gmail
          </span>
          <span>
            <CalendarIcon />
            Calendar
          </span>
          <span>
            <DriveIcon />
            Drive
          </span>
          <span>
            <FileText size={18} />
            Documents
          </span>
        </div>
        {mockAvailable ? (
          <>
            <button
              className="button primary signin-action"
              onClick={() => demo.mutate()}
              disabled={demo.isPending}
            >
              {demo.isPending ? (
                <Spinner label="Opening demo" />
              ) : (
                <>
                  Explore demo <ArrowRight size={18} />
                </>
              )}
            </button>
            <p className="signin-note">
              Synthetic Northstar Labs data. No Google account required.
            </p>
          </>
        ) : (
          <>
            <a className="button primary signin-action" href="/api/auth/google/start">
              Sign in with Google <ArrowRight size={18} />
            </a>
            <p className="signin-note">Choose connector access after signing in.</p>
          </>
        )}
        {demo.isError && <ErrorNotice error={demo.error} retry={() => demo.mutate()} />}
        <div className="signin-control">
          <ShieldCheck size={19} />
          <span>Sending, inviting, and sharing always ask for your approval.</span>
        </div>
      </div>
      <div className="signin-footer">
        MCP Workspace AI <span>Local-first · Transparent by design</span>
      </div>
    </main>
  );
}
