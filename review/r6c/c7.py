import functools, http.server, json, os, socketserver, subprocess, sys, threading
from playwright.sync_api import sync_playwright
DOCS = os.path.abspath(sys.argv[1]); HERE = os.path.dirname(os.path.abspath(__file__))
P6 = json.loads(subprocess.run(["node", os.path.join(HERE, "plans.js"), os.path.join(DOCS, "js", "nodes.js")], capture_output=True, text=True, check=True).stdout)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Q, directory=DOCS)); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(); ctx.route("**/tier579_glyph.rsx", lambda r: r.fulfill(status=404, body=""))
    pg = ctx.new_page(); pg.goto(base + "/player.html?profile=personal"); pg.evaluate("(p) => localStorage.setItem('rsos.plan', JSON.stringify(p))", P6["dx"]); pg.reload(); pg.wait_for_timeout(1000)
    pg.evaluate("() => { $('program').value = 'override'; $('program').dispatchEvent(new Event('change')); }"); pg.wait_for_timeout(300)
    pg.click("#start"); pg.wait_for_timeout(600)
    print(json.dumps({"strict": pg.evaluate("RSOSLineage.strict"), "msg": pg.evaluate("$('compileMsg').textContent")}))
    b.close()
