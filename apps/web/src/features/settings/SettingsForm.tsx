import { type Session, type Settings } from '@mcp-workspace/shared-types';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Check, Settings2, Trash2 } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { Chip } from '../../components/ui/Chip';
import { ClockIcon } from '../../components/ui/ClockIcon';
import { ErrorNotice } from '../../components/ui/ErrorNotice';
import { Spinner } from '../../components/ui/Spinner';
import { api } from '../../services/api';

export function SettingsForm({ settings, session }: { settings: Settings; session: Session }) {
  const client = useQueryClient();
  const [timezone, setTimezone] = useState(settings.timezone);
  const [consent, setConsent] = useState(settings.llm_consent);
  const [validation, setValidation] = useState('');
  const save = useMutation({
    mutationFn: () => api.updateSettings({ timezone, llm_consent: consent }),
    onSuccess: (value) => {
      client.setQueryData(['settings'], value);
      void client.invalidateQueries({ queryKey: ['session'] });
    },
  });
  const erase = useMutation({
    mutationFn: api.deleteAccount,
    onSuccess: () => {
      client.clear();
      window.location.hash = '';
      window.location.reload();
    },
  });
  function submit(event: FormEvent) {
    event.preventDefault();
    try {
      Intl.DateTimeFormat('en-US', { timeZone: timezone }).format();
      setValidation('');
      save.mutate();
    } catch {
      setValidation('Enter a valid IANA timezone, such as America/Chicago.');
    }
  }
  return (
    <div className="settings-layout">
      <form onSubmit={submit}>
        <section className="settings-section">
          <div className="section-title">
            <Settings2 size={19} />
            <h2>Model & context</h2>
          </div>
          <dl className="settings-values">
            <dt>Provider</dt>
            <dd>{settings.provider}</dd>
            <dt>Model</dt>
            <dd>{settings.model}</dd>
            <dt>Context destination</dt>
            <dd>{settings.provider_url}</dd>
            <dt>Runtime mode</dt>
            <dd>
              <Chip tone={['mock', 'demo'].includes(session.mode) ? 'demo' : ''}>
                {session.mode}
              </Chip>
            </dd>
          </dl>
          <p className="muted">
            Provider and model are configured on the server. API keys are never displayed in this
            workspace.
          </p>
          <label className="consent-control">
            <input
              type="checkbox"
              checked={consent}
              onChange={(event) => setConsent(event.target.checked)}
            />
            <span>
              <strong>Allow workspace context to be sent to the configured LLM provider</strong>
              <small>
                Live messages and documents may leave this server for model processing. Review your
                provider’s data terms before enabling. Mock mode uses synthetic data and a local
                deterministic provider.
              </small>
            </span>
          </label>
        </section>
        <section className="settings-section">
          <div className="section-title">
            <ClockIcon />
            <h2>Time & scheduling</h2>
          </div>
          <label className="field-label" htmlFor="timezone">
            Timezone
          </label>
          <input
            className="text-input"
            id="timezone"
            value={timezone}
            onChange={(event) => setTimezone(event.target.value)}
            placeholder="America/Chicago"
            required
            aria-describedby="timezone-help"
          />
          <p className="muted" id="timezone-help">
            Use an IANA timezone. Exact dates and timezones are shown before meeting invitations are
            approved.
          </p>
          {validation && (
            <p className="danger" role="alert">
              {validation}
            </p>
          )}
        </section>
        <div className="settings-save">
          <button className="button primary" type="submit" disabled={save.isPending}>
            {save.isPending ? <Spinner label="Saving" /> : 'Save preferences'}
          </button>
          {save.isSuccess && (
            <span className="saved-message" role="status">
              <Check size={16} />
              Preferences saved
            </span>
          )}
        </div>
        {save.isError && <ErrorNotice error={save.error} />}
      </form>
      <section className="settings-section danger-zone">
        <div className="section-title">
          <Trash2 size={18} />
          <h2>Delete local account data</h2>
        </div>
        <p>
          Delete this account’s conversations, pending approvals, generated files, and stored
          credentials. Google-side files and messages are not removed.
        </p>
        <button
          className="button danger"
          disabled={erase.isPending}
          onClick={() => {
            if (
              window.confirm(
                'Permanently delete all of your local workspace data and sign out? This cannot be undone.',
              )
            )
              erase.mutate();
          }}
        >
          Delete my local data
        </button>
        {erase.isError && <ErrorNotice error={erase.error} />}
      </section>
    </div>
  );
}
