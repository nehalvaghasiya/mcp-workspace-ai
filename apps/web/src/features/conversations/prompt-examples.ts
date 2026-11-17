import { Clock3, FileText, MessageSquare, ShieldCheck } from 'lucide-react';

export const examples = [
  {
    icon: MessageSquare,
    title: 'Catch up on email',
    text: 'Summarize my five most recent inbox emails and highlight decisions and next steps.',
    requires: ['gmail'],
  },
  {
    icon: Clock3,
    title: 'See the week clearly',
    text: 'Check my meetings this week and identify any scheduling conflicts.',
    requires: ['calendar'],
  },
  {
    icon: FileText,
    title: 'Find useful context',
    text: 'Help me find a document in Drive and summarize it. Ask which topic or document to look for.',
    requires: ['drive'],
  },
  {
    icon: ShieldCheck,
    title: 'Prepare a thoughtful follow-up',
    text: 'Help me prepare a reply to an email I select. Ask which message, then show me the proposed reply.',
    requires: ['gmail'],
  },
];
