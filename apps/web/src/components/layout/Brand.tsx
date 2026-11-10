import { Command } from 'lucide-react';

export function Brand() {
  return (
    <div className="brand">
      <span className="brand-mark">
        <Command size={20} />
      </span>
      <span>
        Workspace<span className="brand-ai">AI</span>
        <small>MCP CONNECTED</small>
      </span>
    </div>
  );
}
