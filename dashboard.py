"""
dashboard.py — live web dashboard for benchmark runs.

Zero extra dependencies — pure stdlib HTTP server with SSE.
Opens localhost:8080 automatically when --web flag is passed to benchmark.py.
"""

import json
import os
import queue
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>benchmark — boolean-algebra-engine</title>
<style>
  :root {
    --bg:      #0d1117;
    --surface: #161b22;
    --border:  #30363d;
    --text:    #e6edf3;
    --dim:     #7d8590;
    --green:   #3fb950;
    --red:     #f85149;
    --yellow:  #e3b341;
    --blue:    #388bfd;
    --cyan:    #39c5cf;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'SF Mono', 'Cascadia Code', Consolas, monospace;
    font-size: 13px;
    padding: 24px;
    max-width: 1100px;
    margin: 0 auto;
  }
  h1 { font-size: 18px; font-weight: 600; margin-bottom: 4px; }
  .subtitle { color: var(--dim); font-size: 12px; margin-bottom: 24px; }

  .panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 16px;
    margin-bottom: 16px;
  }
  .panel-title {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: var(--blue);
    font-weight: 600;
    margin-bottom: 12px;
  }

  .config-grid {
    display: grid;
    grid-template-columns: max-content 1fr;
    gap: 4px 24px;
  }
  .ck { color: var(--dim); }
  .cv { color: var(--text); }

  .progress-track {
    height: 4px;
    background: var(--border);
    border-radius: 2px;
    margin: 14px 0 8px;
    overflow: hidden;
  }
  .progress-fill {
    height: 100%;
    background: var(--blue);
    border-radius: 2px;
    transition: width .3s ease, background .3s ease;
    width: 0%;
  }
  .progress-text {
    color: var(--dim);
    font-size: 12px;
    display: flex;
    justify-content: space-between;
  }
  .rate { font-weight: 600; }
  .rate.red    { color: var(--red); }
  .rate.yellow { color: var(--yellow); }
  .rate.green  { color: var(--green); }

  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  thead th {
    text-align: left;
    padding: 6px 8px;
    color: var(--dim);
    border-bottom: 1px solid var(--border);
    font-weight: normal;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: .05em;
  }
  tbody tr {
    border-bottom: 1px solid var(--border);
    animation: fadeIn .2s ease;
  }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(-3px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  tbody td { padding: 7px 8px; white-space: nowrap; }
  .ok  { color: var(--green); }
  .err { color: var(--red); }
  .dim { color: var(--dim); }
  .expr { max-width: 160px; overflow: hidden; text-overflow: ellipsis; }
  .vars { color: var(--cyan); font-size: 11px; }

  .stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 0;
  }
  .stat {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 14px;
    text-align: center;
  }
  .stat-val  { font-size: 30px; font-weight: 700; line-height: 1; margin-bottom: 4px; }
  .stat-lbl  { color: var(--dim); font-size: 11px; text-transform: uppercase; letter-spacing: .06em; }

  .chart-img {
    width: 100%;
    border-radius: 6px;
    border: 1px solid var(--border);
    margin-top: 16px;
  }

  #waiting {
    color: var(--dim);
    text-align: center;
    padding: 64px;
    font-size: 14px;
  }
  .dot { animation: blink 1.2s infinite; display: inline-block; }
  .dot:nth-child(2) { animation-delay: .2s; }
  .dot:nth-child(3) { animation-delay: .4s; }
  @keyframes blink {
    0%, 80%, 100% { opacity: 0; }
    40%  { opacity: 1; }
  }
</style>
</head>
<body>

<h1>boolean-algebra-engine benchmark</h1>
<div class="subtitle">live hallucination detection &mdash; engine is ground truth</div>

<div id="waiting">connecting<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></div>

<div id="main" style="display:none">

  <div class="panel" id="config-panel">
    <div class="panel-title">config</div>
    <div class="config-grid" id="config-grid"></div>
    <div class="progress-track"><div class="progress-fill" id="pfill"></div></div>
    <div class="progress-text">
      <span id="pcount">0 / 0 cases</span>
      <span class="rate" id="prate">&mdash;</span>
    </div>
  </div>

  <div class="panel">
    <div class="panel-title">cases</div>
    <table>
      <thead>
        <tr>
          <th>#</th><th></th><th>Rule 1</th><th>Rule 2</th><th>vars</th><th>engine</th><th>llm</th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>

  <div id="summary-section" style="display:none">
    <div class="panel">
      <div class="panel-title">results</div>
      <div class="stat-grid" id="stat-grid"></div>
      <img id="chart-img" class="chart-img" style="display:none" alt="benchmark chart">
    </div>
  </div>

</div>

<script>
let completed = 0, total = 0, wrong = 0;

const src = new EventSource('/events');

src.onopen = () => {
  document.getElementById('waiting').style.display = 'none';
  document.getElementById('main').style.display = 'block';
};

src.onmessage = e => {
  const d = JSON.parse(e.data);
  if (d.type === 'config')   onConfig(d);
  if (d.type === 'case')     onCase(d);
  if (d.type === 'summary')  onSummary(d);
  if (d.type === 'chart')    loadChart();
};

function onConfig(d) {
  total = d.total;
  const vars = d.variables.join(', ');
  document.getElementById('config-grid').innerHTML = `
    <span class="ck">model</span>        <span class="cv">${d.model}</span>
    <span class="ck">cases</span>        <span class="cv">${d.total} &nbsp;<span style="color:var(--dim)">(${d.n_conflict} conflict &middot; ${d.n_compat} compatible)</span></span>
    <span class="ck">variables</span>   <span class="cv">${d.variables.length} &nbsp;<span style="color:var(--dim)">(${vars})</span></span>
    <span class="ck">temperature</span> <span class="cv" style="color:var(--dim)">0 (deterministic)</span>
    <span class="ck">workers</span>     <span class="cv">${d.workers} parallel</span>
  `;
  tick();
}

function onCase(d) {
  completed++;
  if (!d.correct) wrong++;

  const vars = [...new Set((d.e1 + d.e2).match(/[A-Z]/g) || [])].sort().join(' ');
  const mark = d.correct
    ? '<span class="ok">&#10003;</span>'
    : '<span class="err">&#10007;</span>';
  const eng  = d.ground_truth ? '<span class="ok">yes</span>' : '<span class="err">no</span>';
  const llmV = d.llm ? 'yes' : 'no';
  const llmC = d.correct ? 'dim' : 'err';

  const row = document.createElement('tr');
  row.innerHTML = `
    <td class="dim">${d.idx}</td>
    <td>${mark}</td>
    <td class="expr">${d.e1}</td>
    <td class="expr">${d.e2}</td>
    <td class="vars">${vars}</td>
    <td>${eng}</td>
    <td class="${llmC}">${llmV}</td>
  `;
  document.getElementById('tbody').appendChild(row);
  row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  tick();
}

function tick() {
  const pct = total ? completed / total * 100 : 0;
  document.getElementById('pfill').style.width = pct + '%';
  document.getElementById('pcount').textContent = `${completed} / ${total} cases`;
  if (completed > 0) {
    const r = wrong / completed * 100;
    const cls = r > 30 ? 'red' : r > 15 ? 'yellow' : 'green';
    const el = document.getElementById('prate');
    el.className = 'rate ' + cls;
    el.textContent = r.toFixed(1) + '% hallucination';
  }
}

function onSummary(d) {
  document.getElementById('summary-section').style.display = 'block';
  const col = d.hallucination_rate > 30 ? 'var(--red)' : d.hallucination_rate > 15 ? 'var(--yellow)' : 'var(--green)';
  document.getElementById('stat-grid').innerHTML = `
    <div class="stat"><div class="stat-val" style="color:${col}">${d.hallucination_rate.toFixed(1)}%</div><div class="stat-lbl">hallucination rate</div></div>
    <div class="stat"><div class="stat-val" style="color:var(--green)">${d.correct}</div><div class="stat-lbl">correct</div></div>
    <div class="stat"><div class="stat-val" style="color:var(--red)">${d.hallucinated}</div><div class="stat-lbl">hallucinated</div></div>
    <div class="stat"><div class="stat-val" style="color:var(--text)">${d.total}</div><div class="stat-lbl">total cases</div></div>
  `;
  const fill = document.getElementById('pfill');
  fill.style.width = '100%';
  fill.style.background = col;
}

function loadChart() {
  const img = document.getElementById('chart-img');
  img.src = '/chart?' + Date.now();
  img.style.display = 'block';
}
</script>
</body>
</html>
"""


class Dashboard:
    def __init__(self, port: int = 8080):
        self.port = port
        self._clients: list = []
        self._history: list = []
        self._lock = threading.Lock()
        self._chart_path: Optional[str] = None
        self._server: HTTPServer | None = None

    def start(self, open_browser: bool = True):
        dashboard = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/":
                    body = _HTML.encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

                elif self.path.startswith("/events"):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Connection", "keep-alive")
                    self.end_headers()

                    q: queue.Queue = queue.Queue()
                    with dashboard._lock:
                        for event in dashboard._history:
                            q.put(event)
                        dashboard._clients.append(q)

                    try:
                        while True:
                            try:
                                data = q.get(timeout=25)
                                if data is None:
                                    break
                                self.wfile.write(
                                    f"data: {json.dumps(data)}\n\n".encode()
                                )
                                self.wfile.flush()
                            except queue.Empty:
                                self.wfile.write(b": keepalive\n\n")
                                self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                    finally:
                        with dashboard._lock:
                            if q in dashboard._clients:
                                dashboard._clients.remove(q)

                elif self.path.startswith("/chart"):
                    path = dashboard._chart_path
                    if path and os.path.exists(path):
                        with open(path, "rb") as f:
                            body = f.read()
                        self.send_response(200)
                        self.send_header("Content-Type", "image/png")
                        self.send_header("Content-Length", str(len(body)))
                        self.end_headers()
                        self.wfile.write(body)
                    else:
                        self.send_response(404)
                        self.end_headers()
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, *_):
                pass

        self._server = HTTPServer(("", self.port), Handler)
        thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        thread.start()

        if open_browser:
            try:
                threading.Timer(0.5, lambda: webbrowser.open(f"http://localhost:{self.port}")).start()
            except Exception:
                pass

    def _broadcast(self, event: dict):
        with self._lock:
            self._history.append(event)
            for q in self._clients:
                q.put(event)

    def push_config(self, model: str, total: int, n_conflict: int, n_compat: int,
                    variables: list, workers: int):
        self._broadcast({
            "type": "config",
            "model": model,
            "total": total,
            "n_conflict": n_conflict,
            "n_compat": n_compat,
            "variables": variables,
            "workers": workers,
        })

    def push_case(self, idx: int, e1: str, e2: str, ground_truth: bool,
                  llm: bool, correct: bool):
        self._broadcast({
            "type": "case",
            "idx": idx,
            "e1": e1,
            "e2": e2,
            "ground_truth": ground_truth,
            "llm": llm,
            "correct": correct,
        })

    def push_summary(self, summary: dict, chart_path: Optional[str] = None):
        self._chart_path = chart_path
        safe = {k: v for k, v in summary.items() if k != "results"}
        self._broadcast({"type": "summary", **safe})
        if chart_path and os.path.exists(chart_path):
            self._broadcast({"type": "chart"})

    def stop(self):
        with self._lock:
            for q in self._clients:
                q.put(None)
        if self._server:
            self._server.shutdown()
