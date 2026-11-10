import { Boxes, FileText, MessageSquare, Plug, ShieldCheck } from 'lucide-react';

export type Page = 'chat' | 'artifacts' | 'connectors' | 'mcp' | 'approvals' | 'settings';

export const navigation = [
  { id: 'chat', label: 'Workspace', icon: MessageSquare },
  { id: 'artifacts', label: 'Artifacts', icon: FileText },
  { id: 'connectors', label: 'Connectors', icon: Plug },
  { id: 'mcp', label: 'MCP Explorer', icon: Boxes },
  { id: 'approvals', label: 'Approvals', icon: ShieldCheck },
] as const;

export const pageNames: Record<Page, string> = {
  chat: 'Workspace',
  artifacts: 'Artifact library',
  connectors: 'Connectors',
  mcp: 'MCP Explorer',
  approvals: 'Approval center',
  settings: 'Settings',
};

export function currentPage(): Page {
  const path = window.location.hash.slice(1);
  return Object.keys(pageNames).includes(path) ? (path as Page) : 'chat';
}
