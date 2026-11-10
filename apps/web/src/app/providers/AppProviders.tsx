import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';
import { ErrorBoundary } from '../../components/ui/ErrorBoundary';

const client = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 15000 }, mutations: { retry: false } },
});

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    </ErrorBoundary>
  );
}
