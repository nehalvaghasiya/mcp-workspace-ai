import { type Session } from '@mcp-workspace/shared-types';
import { useQuery } from '@tanstack/react-query';
import { PageHeading } from '../../components/layout/PageHeading';
import { ErrorNotice } from '../../components/ui/ErrorNotice';
import { Spinner } from '../../components/ui/Spinner';
import { SettingsForm } from '../../features/settings/SettingsForm';
import { api } from '../../services/api';

export function SettingsPage({ session }: { session: Session }) {
  const settings = useQuery({
    queryKey: ['settings'],
    queryFn: ({ signal }) => api.settings(signal),
  });
  return (
    <>
      <PageHeading
        eyebrow="MAKE IT YOURS"
        title="Your workspace preferences."
        description="Model settings, data sharing consent, and the timezone your plans use."
      />
      {settings.isPending ? (
        <Spinner label="Loading settings" />
      ) : settings.isError ? (
        <ErrorNotice error={settings.error} retry={() => void settings.refetch()} />
      ) : (
        <SettingsForm
          key={JSON.stringify(settings.data)}
          settings={settings.data}
          session={session}
        />
      )}
    </>
  );
}
