import { type Json } from '@mcp-workspace/shared-types';

export function JsonBlock({ value }: { value: Json | object }) {
  return (
    <pre className="json-block" tabIndex={0}>
      <code>{JSON.stringify(value, null, 2)}</code>
    </pre>
  );
}
