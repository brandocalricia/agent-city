"""grok-build/comms/comms.py, the Agent City <-> Grok Build message link: header parsing, dedupe, cursor, ETag
(304) polling, single-instance lock, backoff, rate limits, send with and without the webhook, setup parsing, and
that secrets (gh token, webhook URL path, sender key) are never printed. Uses a fake `gh` and local HTTP servers."""
import fcntl, http.server, json, os, stat, sys, threading, time, unittest
from helpers import GB, TempDir, run

sys.path.insert(0, os.path.join(GB, "comms"))
import comms  # noqa: E402

COMMS = os.path.join(GB, "comms", "comms.py")
TOKEN = "ghtok_SECRET_123"
KEY = "sk_SECRET_KEY_987654"
FAKE_GH = r"""#!/bin/sh
echo "$*" >> "$FAKE_GH_DIR/args"
case "$1" in
  auth) [ -n "$FAKE_GH_NOAUTH" ] && { echo "You are not logged into any GitHub hosts" >&2; exit 1; }
        echo "ghtok_SECRET_123" ;;
  api) if [ "$2" = "--method" ]; then
         cat > "$FAKE_GH_DIR/body.json"
         [ -n "$FAKE_GH_FAIL" ] && { echo "gh: Server Error (HTTP 502)" >&2; exit 1; }
         echo '{"id": 99, "html_url": "https://github.com/o/r/issues/1#issuecomment-99"}'
       else echo 1; fi ;;
esac
"""


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, text):
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)


def comment(cid, frm, mid, text, re_id="-", created="2026-10-08T05:00:00Z"):
    return {"id": cid, "created_at": created, "updated_at": created,
            "body": "[from:%s] [id:%s] [re:%s]\n%s" % (frm, mid, re_id, text) if frm else text}


class Server:
    """Tiny HTTP server: a fake GitHub comments API (ETag/304) or a webhook receiver."""
    def __init__(self, kind):
        self.kind, self.requests, self.comments, self.fail, self.status = kind, [], [], 0, 200
        outer = self

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                outer.requests.append({"path": self.path, "headers": dict(self.headers)})
                if outer.fail > 0:
                    outer.fail -= 1
                    self.send_response(500); self.end_headers(); return
                body = json.dumps(outer.comments).encode()
                etag = '"%d"' % hash(body)
                if self.headers.get("If-None-Match") == etag:
                    self.send_response(304); self.end_headers(); return
                self.send_response(200); self.send_header("ETag", etag); self.end_headers(); self.wfile.write(body)

            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                outer.requests.append({"path": self.path, "headers": dict(self.headers), "body": self.rfile.read(n)})
                self.send_response(outer.status); self.end_headers(); self.wfile.write(b"{}")

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = "http://127.0.0.1:%d" % self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown(); self.httpd.server_close()


class Base(unittest.TestCase):
    def setUp(self):
        self.t = TempDir(); self.d = self.t.__enter__()
        self.G = os.path.join(self.d, ".grok"); self.D = os.path.join(self.G, "agent-city")
        self.bin = os.path.join(self.d, "bin"); os.makedirs(self.bin)
        p = os.path.join(self.bin, "gh"); write(p, FAKE_GH); os.chmod(p, 0o755)
        self.e = dict(os.environ, HOME=self.d, GROK_HOME=self.G, FAKE_GH_DIR=self.d,
                      PATH=self.bin + os.pathsep + "/usr/bin:/bin", PYTHONDONTWRITEBYTECODE="1")
        self.servers = []
        os.environ["GROK_HOME"] = self.G

    def tearDown(self):
        for s in self.servers:
            s.close()
        os.environ.pop("GROK_HOME", None)
        self.t.__exit__()

    def server(self, kind):
        s = Server(kind); self.servers.append(s); return s

    def comms(self, *args, e=None, input=None):
        r = run([sys.executable, COMMS] + list(args), e or self.e, input=input)
        self.assertNotIn("Traceback", r.stdout + r.stderr)
        for secret in (TOKEN, KEY, "/hooks/SECRETPATH"):
            self.assertNotIn(secret, r.stdout + r.stderr, "secret printed")
        return r

    def webhook(self, status=200, header=None):
        s = self.server("hook"); s.status = status
        args = ["setup", "--url", s.url + "/hooks/SECRETPATH", "--key", KEY] + (["--header", header] if header else [])
        r = self.comms(*args)
        self.assertEqual(r.returncode, 0, r.stdout)
        return s


class Protocol(unittest.TestCase):
    def test_header_variants(self):
        m = comms.parse_message("[from:grok-bot] [id:b1x2] [re:-]\nhello\nworld")
        self.assertEqual(m, {"from": "grok-bot", "id": "b1x2", "re": "-", "text": "hello\nworld"})
        self.assertEqual(comms.parse_message("\ufeff [FROM: Grok-Bot ][id: b1 ] [re:g9]\r\nhi\r\n")["re"], "g9")
        self.assertEqual(comms.parse_message("[from:grok-build] [id:g1] [re:b1]")["text"], "")
        for bad in ("hello", "[from:someone] [id:x] [re:-]\nx", "[from:grok-bot] [id:a b] [re:-]\nx",
                    "[from:grok-bot] [re:-] [id:x]\nx", "> [from:grok-bot] [id:x] [re:-]", None, 42):
            self.assertIsNone(comms.parse_message(bad), bad)

    def test_make_body_round_trips(self):
        body = comms.make_body("g1a2b3", "b7", "line one\nline two")
        self.assertEqual(comms.parse_message(body), {"from": "grok-build", "id": "g1a2b3", "re": "b7", "text": "line one\nline two"})


class Process(Base):
    def test_dedupe_cursor_own_and_headerless(self):
        st = {"last_id": 0, "since": "x", "seen_ids": []}
        cs = [comment(10, "grok-bot", "b1", "first"), comment(11, "grok-build", "g1", "mine"),
              comment(12, None, None, "a plain note"), comment(13, "grok-bot", "b2", "multi\nline")]
        lines = comms.process(st, cs)
        self.assertEqual(len(lines), 2)
        self.assertIn("id:b1 re:- | first", lines[0])
        self.assertIn("multi \u23ce line", lines[1]); self.assertIn("[full text:", lines[1])
        self.assertTrue(all("\n" not in l for l in lines))
        self.assertEqual(st["last_id"], 13)
        # the same comments again (since is inclusive), an edit of an old one, and a re-posted message id
        again = cs + [dict(comment(10, "grok-bot", "b1", "EDITED")), comment(14, "grok-bot", "b2", "repost")]
        self.assertEqual(comms.process(st, again), [])
        self.assertEqual(st["last_id"], 14)

    def test_burst_is_capped(self):
        st = {"last_id": 0, "seen_ids": []}
        lines = comms.process(st, [comment(i, "grok-bot", "b%d" % i, "m%d" % i) for i in range(1, 16)])
        self.assertEqual(len(lines), comms.MAX_PER_POLL + 1)
        self.assertIn("5 older", lines[0]); self.assertIn("m15", lines[-1])

    def test_long_message_truncated_full_text_saved(self):
        st = {"last_id": 0, "seen_ids": []}
        line = comms.process(st, [comment(1, "grok-bot", "b1", "x" * 5000)])[0]
        self.assertLess(len(line), comms.MAX_LINE + 300)
        p = line.split("[full text: ")[1].rstrip("]")
        self.assertIn("x" * 5000, read(p))

    def test_corrupt_state_is_set_aside(self):
        os.makedirs(self.D); write(os.path.join(self.D, "comms-state.json"), "{broken")
        s = comms.load_state()
        self.assertEqual(s["last_id"], 0)
        self.assertTrue(os.path.exists(os.path.join(self.D, "comms-state.json.bad")))


class Backoff(unittest.TestCase):
    def test_next_delay(self):
        self.assertEqual(comms.next_delay(0), 10)
        self.assertEqual([comms.next_delay(n) for n in (1, 2, 3, 4, 5, 9)], [20, 40, 80, 160, 300, 300])

    def test_classify(self):
        self.assertIsNone(comms.classify_http(304, {}))
        self.assertIsInstance(comms.classify_http(500, {}), comms.Transient)
        self.assertIsInstance(comms.classify_http(401, {}), comms.AuthError)
        self.assertIsInstance(comms.classify_http(404, {}), comms.AuthError)
        r = comms.classify_http(403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1100"}, now=1000)
        self.assertIsInstance(r, comms.RateLimited); self.assertEqual(r.wait, 101)
        self.assertEqual(comms.classify_http(429, {"Retry-After": "30"}).wait, 30)

    def test_token_only_sent_to_github_or_localhost(self):
        self.assertTrue(comms.token_allowed("https://api.github.com"))
        self.assertTrue(comms.token_allowed("http://127.0.0.1:9"))
        self.assertFalse(comms.token_allowed("https://evil.example"))


class Watch(Base):
    def watch(self, api, n=3, extra=None):
        e = dict(self.e, AGENT_CITY_COMMS_API=api.url, **(extra or {}))
        return self.comms("watch", "--interval", "0.05", "--iterations", str(n), e=e)

    def test_delivers_once_then_304(self):
        api = self.server("api")
        api.comments = [comment(5, "grok-bot", "b1", "Link is up, reply with ping to test."), comment(6, "grok-build", "g1", "pong")]
        r = self.watch(api)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.count("[agent-city] message from Agent City"), 1, r.stdout)
        self.assertEqual(r.stderr, "")
        self.assertEqual(api.requests[0]["headers"]["Authorization"], "Bearer " + TOKEN)
        self.assertIn("since=", api.requests[0]["path"])
        self.assertTrue(any("If-None-Match" in q["headers"] for q in api.requests[1:]), "no conditional request")
        st = json.loads(read(os.path.join(self.D, "comms-state.json")))
        self.assertEqual(st["last_id"], 6)
        self.assertEqual(stat.S_IMODE(os.stat(os.path.join(self.D, "comms-state.json")).st_mode), 0o600)
        # restart: nothing is repeated; a new message is delivered
        api.comments.append(comment(7, "grok-bot", "b2", "second", "g1", "2026-10-08T05:01:00Z"))
        r = self.watch(api, 2)
        self.assertNotIn("Link is up", r.stdout); self.assertIn("id:b2 re:g1 | second", r.stdout)

    def test_backoff_survives_errors(self):
        api = self.server("api"); api.fail = 3
        api.comments = [comment(5, "grok-bot", "b1", "after the outage")]
        e = dict(self.e, AGENT_CITY_COMMS_API=api.url)
        r = self.comms("watch", "--interval", "0.01", "--iterations", "5", e=e)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.count("offline"), 1)
        self.assertIn("after the outage", r.stdout); self.assertIn("back online", r.stdout)

    def test_single_instance(self):
        os.makedirs(self.D)
        f = open(os.path.join(self.D, "comms-watch.lock"), "a+"); fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        f.write("4242"); f.flush()
        try:
            t = time.time()
            r = self.watch(self.server("api"), 50)
            self.assertEqual(r.returncode, 0)
            self.assertIn("already running (pid 4242)", r.stdout)
            self.assertLess(time.time() - t, 5)
        finally:
            f.close()

    def test_gh_missing_or_signed_out(self):
        api = self.server("api")
        e = dict(self.e, PATH=os.path.join(self.d, "empty"), AGENT_CITY_COMMS_API=api.url)   # no gh anywhere
        r = self.comms("watch", "--iterations", "1", e=e)
        self.assertEqual(r.returncode, 2); self.assertIn("brew install gh", r.stdout)
        r = self.watch(api, 1, {"FAKE_GH_NOAUTH": "1"})
        self.assertEqual(r.returncode, 2); self.assertIn("gh auth login", r.stdout)
        self.assertEqual(api.requests, [])

    def test_refuses_foreign_api_host(self):
        e = dict(self.e, AGENT_CITY_COMMS_API="https://evil.example")
        r = self.comms("watch", "--iterations", "1", e=e)
        self.assertEqual(r.returncode, 2)


class Send(Base):
    def body(self):
        return json.loads(read(os.path.join(self.d, "body.json")))["body"]

    def test_without_webhook_comment_still_works(self):
        r = self.comms("send", "--re", "b1", "pong")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("comment: posted", r.stdout); self.assertIn("webhook: not configured", r.stdout)
        m = comms.parse_message(self.body())
        self.assertEqual((m["from"], m["re"], m["text"]), ("grok-build", "b1", "pong"))
        self.assertRegex(m["id"], r"^g[0-9a-f]{6}$")
        self.assertIn("repos/brandocalricia/agent-city-comms/issues/1/comments", read(os.path.join(self.d, "args")))

    def test_webhook_default_header_and_payload(self):
        hook = self.webhook()
        r = self.comms("send", "-", input="multi\nline 'quotes' $HOME `x`")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("webhook: delivered (HTTP 200)", r.stdout)
        q = hook.requests[-1]
        self.assertEqual(q["headers"]["Authorization"], "Bearer " + KEY)
        p = json.loads(q["body"])
        self.assertEqual(p["text"], "multi\nline 'quotes' $HOME `x`"); self.assertEqual(p["re"], "-")
        self.assertEqual(p["id"], comms.parse_message(self.body())["id"])
        self.assertTrue(p["comment_url"].startswith("https://github.com/"))

    def test_custom_header(self):
        hook = self.webhook(header="X-Sender-Key: {key}")
        self.comms("send", "hi")
        self.assertEqual(hook.requests[-1]["headers"]["X-Sender-Key"], KEY)
        self.assertNotIn("Authorization", hook.requests[-1]["headers"])

    def test_webhook_failure_is_reported_comment_kept(self):
        hook = self.webhook(status=401)
        r = self.comms("send", "hi")
        self.assertEqual(r.returncode, 0)
        self.assertIn("webhook: failed: HTTP 401", r.stdout); self.assertIn("comment: posted", r.stdout)
        self.assertEqual(len(hook.requests), 1)   # 4xx is not retried

    def test_both_fail_exit_1(self):
        os.makedirs(self.D)
        write(os.path.join(self.D, "bot-webhook.env"),
            "AGENT_CITY_WEBHOOK_URL=http://127.0.0.1:9/hooks/SECRETPATH\nAGENT_CITY_WEBHOOK_KEY=%s\n" % KEY)
        r = self.comms("send", "hi", e=dict(self.e, FAKE_GH_FAIL="1"))
        self.assertEqual(r.returncode, 1); self.assertIn("FAILED", r.stdout); self.assertIn("network error", r.stdout)

    def test_rate_limits(self):
        self.assertEqual(self.comms("send", "one").returncode, 0)
        r = self.comms("send", "two")
        self.assertEqual(r.returncode, 3); self.assertIn("rate limit", r.stdout)
        now = time.time()
        write(os.path.join(self.D, "comms-sends.log"), "".join("%.3f\n" % (now - 600 + i * 9) for i in range(60)))
        ok, why = comms.rate_check(now + 1)
        self.assertFalse(ok); self.assertIn("per hour", why)
        self.assertTrue(comms.rate_check(now + 1 + 3600)[0])

    def test_input_validation_and_gh_missing(self):
        self.assertEqual(self.comms("send", "  ").returncode, 2)
        self.assertEqual(self.comms("send", "x" * 7000).returncode, 2)
        self.assertEqual(self.comms("send", "--re", "bad id!", "x").returncode, 2)
        r = self.comms("send", "x", e=dict(self.e, PATH=os.path.join(self.d, "empty")))
        self.assertEqual(r.returncode, 2); self.assertIn("brew install gh", r.stdout)
        r = self.comms("send", "x", e=dict(self.e, FAKE_GH_NOAUTH="1"))
        self.assertEqual(r.returncode, 2); self.assertIn("gh auth login", r.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.d, "body.json")))


class Setup(Base):
    def test_parse_panel_formats(self):
        P = comms.parse_setup
        c = P("curl -X POST 'https://hooks.example/r/abc' -H 'Content-Type: application/json' -H 'Authorization: Bearer %s' -d '{}'" % KEY)
        self.assertEqual((c["header"], c["key"]), ("Authorization: Bearer {key}", KEY))
        c = P('curl https://hooks.example/r/abc --header "X-Routine-Key: <YOUR_KEY>"\nSender key: %s' % KEY)
        self.assertEqual((c["header"], c["key"]), ("X-Routine-Key: {key}", KEY))
        c = P("Webhook URL: https://hooks.example/r/abc\nKey: %s" % KEY)
        self.assertEqual((c["header"], c["key"]), ("Authorization: Bearer {key}", KEY))
        self.assertEqual(P("https://hooks.example/r?key=abc")["header"], "")
        for bad in ("no url here", "http://plain.example/x\nKey: k", "https://hooks.example/r/abc"):
            self.assertRaises(ValueError, P, bad)
        self.assertRaises(ValueError, P, "", url="https://h.example/x", key="k", header="X-Key: nokey")

    def test_setup_from_paste_is_private(self):
        r = self.comms("setup", input="curl -X POST https://hooks.example/hooks/SECRETPATH -H 'Authorization: Bearer %s'" % KEY)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("host hooks.example", r.stdout)
        p = os.path.join(self.D, "bot-webhook.env")
        self.assertEqual(stat.S_IMODE(os.stat(p).st_mode), 0o600)
        self.assertIn(KEY, read(p))
        os.chmod(p, 0o644)
        self.comms("status")
        self.assertEqual(stat.S_IMODE(os.stat(p).st_mode), 0o600)

    def test_bad_paste_writes_nothing(self):
        r = self.comms("setup", input="Authorization: Bearer %s" % KEY)
        self.assertEqual(r.returncode, 2)
        self.assertFalse(os.path.exists(os.path.join(self.D, "bot-webhook.env")))

    def test_status(self):
        r = self.comms("status")
        self.assertEqual(r.returncode, 0)
        for word in ("gh: signed in", "webhook: not configured", "watcher: not running", "sends this hour: 0"):
            self.assertIn(word, r.stdout)


class Hygiene(unittest.TestCase):
    def test_python38_syntax_and_no_secrets_in_repo(self):
        import ast, re
        src = read(COMMS)
        ast.parse(src, feature_version=(3, 8))
        root = os.path.dirname(GB)
        for dirpath, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "tests")]
            for f in files:
                if f.endswith((".py", ".sh", ".md", ".json", ".js", ".env", ".txt")):
                    with open(os.path.join(dirpath, f), errors="replace") as fh:
                        text = fh.read()
                    self.assertIsNone(re.search(r"AGENT_CITY_WEBHOOK_(URL|KEY)=[^\s%\"']{8,}", text), f)
        self.assertFalse(any(f.endswith(".env") for _, _, fs in os.walk(root) for f in fs))


if __name__ == "__main__":
    unittest.main()
