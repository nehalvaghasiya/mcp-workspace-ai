export const connectorDetails: Record<string, { description: string; writeLabel: string }> = {
  gmail: {
    description:
      'Find messages, understand threads, and prepare replies with generated attachments.',
    writeLabel: 'Enable drafting, sending & mailbox changes',
  },
  calendar: {
    description: 'See your schedule, check availability, and manage your meetings.',
    writeLabel: 'Enable event changes',
  },
  drive: {
    description: 'Search your existing Drive files, organize folders, and manage approved sharing.',
    writeLabel: 'Enable file changes & sharing',
  },
  docs: {
    description: 'Read, create, and edit Google documents with headings, lists, and tables.',
    writeLabel: 'Enable document changes',
  },
  sheets: {
    description: 'Read ranges and build spreadsheets with values, formulas, and formatting.',
    writeLabel: 'Enable spreadsheet changes',
  },
  slides: {
    description: 'Read presentations and create or edit decks in Google Slides.',
    writeLabel: 'Enable presentation changes',
  },
};

export const connectorStatus: Record<string, string> = {
  disconnected: 'Not connected',
  not_connected: 'Not connected',
  needs_permission: 'Permission needed',
  connected: 'Connected',
  authorized: 'Authorized · awaiting first request',
  expired: 'Reconnect required',
  error: 'Connection needs attention',
  disabled: 'Disabled',
  mock: 'Synthetic demo',
};
