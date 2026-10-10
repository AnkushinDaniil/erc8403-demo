import http.server, urllib.request, os
ROOT = os.path.dirname(os.path.abspath(__file__))
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def log_message(s, *a): pass
    def do_POST(s):
        b = s.rfile.read(int(s.headers['content-length']))
        port = 8612 if s.path.startswith('/rpc2') else 8621
        r = urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:%d" % port, b, {'content-type': 'application/json'})).read()
        s.send_response(200); s.send_header('content-type', 'application/json'); s.end_headers(); s.wfile.write(r)
    def do_GET(s):
        if s.path.startswith('/account/'): s.path = '/explorer.html'
        if s.path == '/two': s.path = '/two.html'
        return super().do_GET()
http.server.ThreadingHTTPServer(('127.0.0.1', 8700), H).serve_forever()
