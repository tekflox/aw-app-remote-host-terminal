import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import xtermCss from '@xterm/xterm/css/xterm.css?inline';

const WIN_ID = 'remote-host-terminal.main';

export function register(host) {
  const { useCallback, useEffect, useRef, useState } = host.React;
  const api = host.app;

  if (!document.getElementById('aw-remote-host-terminal-xterm-css')) {
    const style = document.createElement('style');
    style.id = 'aw-remote-host-terminal-xterm-css';
    style.textContent = xtermCss;
    document.head.appendChild(style);
  }

  function TerminalPane({ tab, active, onState }) {
    const containerRef = useRef(null);

    useEffect(() => {
      const element = containerRef.current;
      if (!element) return undefined;
      const term = new Terminal({
        convertEol: true,
        cursorBlink: true,
        fontSize: 13,
        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
        theme: { background: '#09090b', foreground: '#e4e4e7' },
      });
      const fit = new FitAddon();
      term.loadAddon(fit);
      term.open(element);
      fit.fit();

      const ws = new WebSocket(api.wsUrl(`/ws/hosts/${encodeURIComponent(tab.host.id)}`));
      const sendResize = () => {
        fit.fit();
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ op: 'resize', cols: term.cols, rows: term.rows }));
        }
      };
      ws.onopen = () => { onState(tab.id, 'connecting'); sendResize(); };
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.op === 'output') term.write(message.data || '');
          if (message.op === 'status') onState(tab.id, message.state || 'disconnected', message.message);
        } catch (_error) { /* Ignore malformed upstream frames. */ }
      };
      ws.onerror = () => onState(tab.id, 'disconnected', 'Connection failed');
      ws.onclose = () => onState(tab.id, 'disconnected');
      const input = term.onData((data) => {
        if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ op: 'input', data }));
      });
      const observer = new ResizeObserver(sendResize);
      observer.observe(element);
      return () => {
        input.dispose();
        observer.disconnect();
        ws.close();
        term.dispose();
      };
    }, [tab.id]);

    return <div ref={containerRef} className={`${active ? 'block' : 'hidden'} absolute inset-0 bg-[#09090b] p-2`} />;
  }

  function RemoteHostTerminalWindow() {
    const [hosts, setHosts] = useState([]);
    const [tabs, setTabs] = useState([]);
    const [activeId, setActiveId] = useState('');
    const [selectedHost, setSelectedHost] = useState('');
    const [error, setError] = useState('');

    const loadHosts = useCallback(async () => {
      setError('');
      try {
        const response = await api.fetch('/hosts');
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
        setHosts(data.hosts || []);
        const firstOnline = (data.hosts || []).find((item) => item.connected);
        setSelectedHost((current) => current || firstOnline?.id || '');
      } catch (cause) { setError(cause.message); }
    }, []);

    useEffect(() => { loadHosts(); }, [loadHosts]);

    const openTab = () => {
      const hostRow = hosts.find((item) => item.id === selectedHost);
      if (!hostRow?.connected) return;
      const id = `${hostRow.id}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
      setTabs((current) => [...current, { id, host: hostRow, state: 'connecting', message: '' }]);
      setActiveId(id);
    };
    const closeTab = (id) => {
      setTabs((current) => {
        const index = current.findIndex((tab) => tab.id === id);
        const next = current.filter((tab) => tab.id !== id);
        if (activeId === id) setActiveId(next[Math.min(index, next.length - 1)]?.id || '');
        return next;
      });
    };
    const updateState = useCallback((id, state, message = '') => {
      setTabs((current) => current.map((tab) => tab.id === id ? { ...tab, state, message } : tab));
    }, []);

    return (
      <div className="h-full min-h-0 flex flex-col bg-[var(--color-bg)] text-[var(--color-text)]">
        <div className="shrink-0 flex items-center gap-2 border-b border-[var(--color-border)] px-3 py-2">
          <select value={selectedHost} onChange={(event) => setSelectedHost(event.target.value)}
            className="min-w-0 flex-1 rounded border border-[var(--color-border)] bg-[var(--color-bg-elevated)] px-2 py-1.5 text-sm">
            <option value="">Select a linked host…</option>
            {hosts.map((item) => <option key={item.id} value={item.id} disabled={!item.connected}>
              {item.hostname || item.workspace_slug || item.id} · {item.os || 'unknown'}{item.connected ? '' : ' · offline'}
            </option>)}
          </select>
          <button onClick={openTab} disabled={!selectedHost}
            className="rounded bg-[var(--color-accent)] px-3 py-1.5 text-sm text-white disabled:opacity-40">Open terminal</button>
          <button onClick={loadHosts} title="Refresh hosts"
            className="rounded border border-[var(--color-border)] px-2 py-1.5 text-sm">↻</button>
        </div>
        {error && <div className="shrink-0 bg-red-500/10 px-3 py-2 text-sm text-red-400">{error}</div>}
        {tabs.length > 0 && <div className="shrink-0 flex overflow-x-auto border-b border-[var(--color-border)] bg-[var(--color-bg-header)]">
          {tabs.map((tab) => <button key={tab.id} onClick={() => setActiveId(tab.id)}
            className={`flex items-center gap-2 border-r border-[var(--color-border)] px-3 py-2 text-xs ${activeId === tab.id ? 'bg-[var(--color-bg)]' : ''}`}>
            <span className={`h-2 w-2 rounded-full ${tab.state === 'connected' ? 'bg-emerald-500' : tab.state === 'connecting' ? 'bg-amber-400' : 'bg-red-500'}`} />
            <span>{tab.host.hostname || tab.host.workspace_slug || tab.host.id}</span>
            <span onClick={(event) => { event.stopPropagation(); closeTab(tab.id); }} className="ml-1 opacity-60 hover:opacity-100">×</span>
          </button>)}
        </div>}
        <div className="relative min-h-0 flex-1">
          {tabs.length === 0 && <div className="absolute inset-0 grid place-items-center text-sm text-[var(--color-text-muted)]">
            Select an online remote host and open a terminal.
          </div>}
          {tabs.map((tab) => <TerminalPane key={tab.id} tab={tab} active={tab.id === activeId} onState={updateState} />)}
        </div>
        {tabs.find((tab) => tab.id === activeId)?.message && <div className="shrink-0 border-t border-[var(--color-border)] px-3 py-1 text-xs text-red-400">
          {tabs.find((tab) => tab.id === activeId).message}
        </div>}
      </div>
    );
  }

  host.registerWindow(WIN_ID, RemoteHostTerminalWindow);
}

export default register;
