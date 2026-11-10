import { Component, type ReactNode } from 'react';

export interface BoundaryState {
  failed: boolean;
}

export class ErrorBoundary extends Component<{ children: ReactNode }, BoundaryState> {
  state: BoundaryState = { failed: false };
  static getDerivedStateFromError(): BoundaryState {
    return { failed: true };
  }
  render() {
    return this.state.failed ? (
      <main className="fatal">
        <h1>The workspace couldn’t display this page.</h1>
        <p>Your saved conversations remain on the server.</p>
        <button className="button primary" onClick={() => window.location.reload()}>
          Reload workspace
        </button>
      </main>
    ) : (
      this.props.children
    );
  }
}
