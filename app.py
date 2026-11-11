#!/usr/bin/env python3
"""
InfoSec Mastery - Command Injection lab ("network tools" ping page).
TWO modes, chosen by the MODE env var:

  MODE=vuln   (default)  builds a shell string from your input -> INJECTABLE
  MODE=secure            calls the binary directly with an argument array
                         + an allow-list -> your input is data, never a command

Try (vuln):  host = 127.0.0.1; id
             host = 127.0.0.1; cat /etc/passwd

EDUCATIONAL USE ONLY. Run only on your own isolated machine.
"""
import os, re, html, subprocess
from flask import Flask, request

app = Flask(__name__)
MODE = os.environ.get("MODE", "vuln").lower()
HOST_RE = re.compile(r"^[A-Za-z0-9.\-]+$")   # letters, digits, dot, dash only

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Network Tools</title>
<style>body{{background:#0b0e14;color:#e6edf3;font-family:system-ui,Arial;margin:0;padding:40px}}
.card{{max-width:760px;margin:auto;background:#111a2b;border:1px solid #223049;border-radius:16px;padding:28px 32px}}
h1{{font-size:22px;margin:0 0 2px}} .sub{{color:#8b98a5;font-size:13px;margin-bottom:18px}}
.row{{display:flex;gap:10px}} input{{flex:1;padding:11px;border-radius:8px;border:1px solid #223049;
background:#0d1626;color:#e6edf3;font-family:ui-monospace,monospace}}
button{{padding:11px 22px;border:0;border-radius:8px;background:#39c5cf;color:#06121a;font-weight:700;cursor:pointer}}
pre{{margin-top:18px;background:#060d16;border:1px solid #223049;border-radius:10px;padding:16px;
white-space:pre-wrap;word-break:break-word;color:#cfe;min-height:40px;font-family:ui-monospace,monospace;font-size:14px}}
.mode{{color:{modecol};font-weight:700}}</style></head>
<body><div class="card"><h1>Network Tools &mdash; Ping</h1>
<div class="sub">Enter a host to ping. &nbsp;mode: <span class="mode">{mode}</span></div>
<form class="row" method="get" action="/ping">
<input name="host" value="{host}" placeholder="e.g. 127.0.0.1" autocomplete="off" autofocus>
<button type="submit">Ping</button></form>
<pre>{out}</pre></div></body></html>"""


def render(host="", out=""):
    modecol = "#ff5a3c" if MODE == "vuln" else "#3fb950"
    return PAGE.format(mode=html.escape(MODE), modecol=modecol,
                       host=html.escape(host, quote=True), out=html.escape(out))


@app.route("/")
def index():
    return render(host="127.0.0.1")


@app.route("/ping")
def ping():
    host = request.args.get("host", "").strip()
    if not host:
        return render(out="(enter a host)")

    if MODE == "secure":
        # input is DATA: validate, then pass as a separate argument (no shell).
        if not HOST_RE.match(host):
            return render(host, out=f"Rejected: '{host}' is not a valid host.\n"
                                    "Allowed: letters, digits, dot, dash.")
        try:
            r = subprocess.run(["ping", "-c", "1", "-W", "2", host],
                               capture_output=True, text=True, timeout=6)
            return render(host, out=(r.stdout + r.stderr) or "(no output)")
        except Exception as e:
            return render(host, out=f"error: {e}")

    # MODE=vuln: input is glued into a shell string -> command injection.
    cmd = f"ping -c 1 -W 2 {host}"
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=6)
        return render(host, out=(r.stdout + r.stderr) or "(no output)")
    except Exception as e:
        return render(host, out=f"error: {e}")


if __name__ == "__main__":
    print(f"[command-injection lab] MODE={MODE} on :8081")
    app.run(host="0.0.0.0", port=8081)
