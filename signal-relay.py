"""Tiny HTTP relay that wraps signal-cli-rest-api's recipients field in an array.

Shoutrrr's generic webhook sends all $key=value params as strings in JSON,
but signal-cli-rest-api requires recipients to be a JSON array. This relay
accepts the flat JSON from Shoutrrr and converts recipients to ["recipients"]
before forwarding to signal-api.
"""

import http.server
import json
import urllib.error
import urllib.request

SIGNAL_API = "http://signal-api:8080/v2/send"


class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if isinstance(data.get("recipients"), str):
            data["recipients"] = [data["recipients"]]
        req = urllib.request.Request(
            SIGNAL_API, json.dumps(data).encode(), {"Content-Type": "application/json"}
        )
        try:
            resp = urllib.request.urlopen(req)
            body = resp.read()
            self.send_response(resp.status)
        except urllib.error.HTTPError as e:
            body = e.read()
            self.send_response(e.code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print("signal-relay listening on :8082", flush=True)
    http.server.HTTPServer(("", 8082), Handler).serve_forever()
