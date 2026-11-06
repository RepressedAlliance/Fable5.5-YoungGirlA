"""Image edit through the OpenAI image API, for the few pictures that need the highest quality. Only generates images.
usage: openai_edit.py INPUT.png PROMPT.txt OUT.png [--n 2]
"""
import argparse
import base64
import json
import os
import urllib.request
import uuid
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("input")
ap.add_argument("prompt")
ap.add_argument("out")
ap.add_argument("--n", type=int, default=1)
ap.add_argument("--model", default="gpt-image-1")
a = ap.parse_args()
key = os.environ["OPENAI_API_KEY"]
b = uuid.uuid4().hex
body = bytearray()


def field(name, value):
    body.extend(f'--{b}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())


field("model", a.model)
field("prompt", Path(a.prompt).read_text(encoding="utf-8"))
field("size", "1536x1024")
field("quality", "high")
field("n", str(a.n))
body.extend(f'--{b}\r\nContent-Disposition: form-data; name="image"; filename="in.png"\r\nContent-Type: image/png\r\n\r\n'.encode())
body.extend(Path(a.input).read_bytes())
body.extend(f"\r\n--{b}--\r\n".encode())
req = urllib.request.Request("https://api.openai.com/v1/images/edits", data=bytes(body),
                             headers={"Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={b}"})
try:
    with urllib.request.urlopen(req, timeout=600) as r:
        data = json.load(r)
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read()[:600])
    raise SystemExit(1)
out = Path(a.out)
out.parent.mkdir(parents=True, exist_ok=True)
for i, d in enumerate(data["data"]):
    p = out if a.n == 1 else out.with_name(f"{out.stem}_{i}{out.suffix}")
    p.write_bytes(base64.b64decode(d["b64_json"]))
    print("OK", p)
