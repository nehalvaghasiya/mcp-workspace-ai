import { LoaderCircle } from 'lucide-react';

export function Spinner({ label = 'Loading' }: { label?: string }) {
  return (
    <span className="loading" role="status">
      <LoaderCircle size={17} className="spin" />
      {label}
    </span>
  );
}
