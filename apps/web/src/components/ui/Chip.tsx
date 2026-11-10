import { type ReactNode } from 'react';

export function Chip({ children, tone = '' }: { children: ReactNode; tone?: string }) {
  return <span className={`chip ${tone}`}>{children}</span>;
}
