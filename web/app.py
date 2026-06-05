"""Minimal adaptive UI placeholder.

Run:
    python web/app.py

Then open http://127.0.0.1:8000
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer

from bench.run import load_scenarios
from moral_agent_os import MoralAgentOS


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib API
        runtime = MoralAgentOS()
        rows = []
        for scenario in load_scenarios():
            decision = runtime.evaluate(scenario)
            rows.append(
                f"<tr><td>{scenario.id}</td><td>{scenario.expected_label}</td>"
                f"<td>{decision.disposition}</td><td>{decision.rationale}</td></tr>"
            )

        html = f"""
        <!doctype html>
        <html>
          <head>
            <title>Moral Agent OS</title>
            <style>
              body {{ font-family: system-ui, sans-serif; margin: 2rem; }}
              table {{ border-collapse: collapse; width: 100%; }}
              th, td {{ border-bottom: 1px solid #ddd; padding: 0.6rem; text-align: left; }}
            </style>
          </head>
          <body>
            <h1>Moral Agent OS</h1>
            <p>Adaptive action routing scaffold.</p>
            <table>
              <thead>
                <tr><th>Scenario</th><th>Label</th><th>Disposition</th><th>Rationale</th></tr>
              </thead>
              <tbody>{''.join(rows)}</tbody>
            </table>
          </body>
        </html>
        """
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = HTTPServer(("127.0.0.1", 8000), Handler)
    print("Serving http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
