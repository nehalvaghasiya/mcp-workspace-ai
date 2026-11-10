import { vi } from 'vitest';
export class FakeSource extends EventTarget {
  static instance: FakeSource;
  onmessage: ((event: MessageEvent<string>) => void) | null = null;
  onopen: (() => void) | null = null;
  onerror: (() => void) | null = null;
  close = vi.fn();
  constructor() {
    super();
    FakeSource.instance = this;
  }
  receive(value: unknown) {
    this.onmessage?.(new MessageEvent('message', { data: JSON.stringify(value) }));
  }
}
