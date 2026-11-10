import { type Approval, type Connector, type Session } from '@mcp-workspace/shared-types';

export interface ChatProps {
  conversationId?: string;
  onSelect: (id?: string) => void;
  connectors: Connector[];
  approvals: Approval[];
  session: Session;
  online: boolean;
}
