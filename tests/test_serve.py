"""The HTTP tool service runs a full meeting_reschedule episode (the reference actions) and returns reward 1."""
import json
import threading
import urllib.request

from eurl.core import load
from eurl.serve import serve


def _post(port, path, payload):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_reference_episode_over_http():
    server = serve(port=0)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as r:
            assert "meeting_reschedule" in json.loads(r.read())["environments"]
        local = load("meeting_reschedule")
        for seed in range(5):
            code, obs = _post(port, "/reset", {"env": "meeting_reschedule", "seed": seed, "split": "dev", "language": "deu"})
            assert code == 200 and obs["tools"] and obs["instruction"]
            local.reset(seed, "dev", "deu")
            assert obs["instruction"] == local.public_prompt()
            reward = None
            for action in local.reference_actions():
                if "final" in action:
                    code, out = _post(port, "/finish", {"session": obs["session"], "final": action["final"]})
                    reward = out["reward"]
                    break
                code, out = _post(port, "/step", {"session": obs["session"], **action})
                assert code == 200 and "error" not in out["observation"], out
            assert reward == 1.0
        assert _post(port, "/step", {"session": "nope", "tool": "list_inbox", "arguments": {}})[0] == 400
        assert _post(port, "/reset", {"env": "finance_amount_due"})[0] == 400
    finally:
        server.shutdown()
