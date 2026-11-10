import { type Connector } from '@mcp-workspace/shared-types';
import { ArrowUp, ShieldCheck, Sparkles } from 'lucide-react';
import { examples } from '../../features/conversations/prompt-examples';

export function Welcome({
  connectors,
  onPrompt,
}: {
  connectors: Connector[];
  onPrompt: (text: string) => void;
}) {
  return (
    <div className="welcome">
      <span className="welcome-symbol">
        <Sparkles size={25} />
      </span>
      <p className="eyebrow">YOUR WORK, WITH A CLEARER VIEW</p>
      <h1>
        What can we make
        <br />
        room for today?
      </h1>
      <p className="welcome-description">
        Find the context. Connect the dots.
        <br />
        Turn your workspace into something useful.
      </p>
      <div className="connector-pills">
        {connectors.map((connector) => (
          <span key={connector.id}>
            <span className={`status-dot ${connector.enabled ? '' : 'disabled'}`} />
            {connector.name}
          </span>
        ))}
      </div>
      <div className="prompt-grid">
        {examples.map(({ icon: Icon, title, text }) => (
          <button
            key={title}
            className="prompt-card"
            onClick={() => {
              onPrompt(text);
            }}
          >
            <Icon size={18} />
            <strong>{title}</strong>
            <span>{text}</span>
            <ArrowUp size={15} />
          </button>
        ))}
      </div>
      <div className="welcome-footnote">
        <ShieldCheck size={14} />
        Read and create freely. Review before anything leaves.
      </div>
    </div>
  );
}
