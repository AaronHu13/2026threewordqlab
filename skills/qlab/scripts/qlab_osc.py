#!/usr/bin/env python3
"""OSC-over-TCP client for QLab 5 (F53OSC = OSC + SLIP framing on port 53000).

Three non-obvious things this handles for you:
  * TCP, not UDP -- port 53000 accepts UDP but replies never arrive.
  * /connect is sent UNSCOPED. Scoping it to /workspace/<id>/connect returns
    "ok:" with no permissions and every later command silently reports denied.
  * Replies are JSON in a string arg; a non-"ok" status is raised, not returned
    as None, so a denied/error command fails loudly.

Usage:
    from qlab_osc import QLab
    q = QLab(workspace="D5B5B229-...", passcode=1234)
    q.send("/cue/1/duration")            # -> value
    q.send("/cue/1/start")               # fire it
    q.send("/version", scoped=False)     # app-level, no workspace prefix

CLI:
    python3 qlab_osc.py /version
    python3 qlab_osc.py --ws <uuid> --passcode 1234 /cue/1/duration
"""
import socket, struct, json, time


def _pad(b):
    """Pad to a multiple of 4, as OSC requires. Note: pad only as needed --
    always appending 4 nulls when already aligned is what parse() below does
    NOT expect, and QLab only tolerates it by accident."""
    return b + b"\0" * (-len(b) % 4)


def _ostr(s):
    return _pad(s.encode("utf-8") + b"\0")


def build(addr, *args):
    tags = ","
    body = b""
    for a in args:
        if isinstance(a, bool):
            tags += "T" if a else "F"
        elif isinstance(a, int):
            tags += "i"; body += struct.pack(">i", a)
        elif isinstance(a, float):
            tags += "f"; body += struct.pack(">f", a)
        else:
            tags += "s"; body += _ostr(str(a))
    return _ostr(addr) + _ostr(tags) + body


def _slip_encode(b):
    out = bytearray([0xC0])
    for x in b:
        if x == 0xC0:
            out += b"\xdb\xdc"
        elif x == 0xDB:
            out += b"\xdb\xdd"
        else:
            out.append(x)
    out.append(0xC0)
    return bytes(out)


def _slip_frames(buf):
    """Split a byte buffer into decoded SLIP frames."""
    frames, cur, esc = [], bytearray(), False
    for x in buf:
        if x == 0xC0:
            if cur:
                frames.append(bytes(cur)); cur = bytearray()
        elif esc:
            cur.append(0xC0 if x == 0xDC else 0xDB if x == 0xDD else x); esc = False
        elif x == 0xDB:
            esc = True
        else:
            cur.append(x)
    return frames


def parse(data):
    def rd(d, i):
        end = d.index(b"\0", i)
        s = d[i:end].decode("utf-8", "replace")
        i = end + 1
        while i % 4:
            i += 1
        return s, i

    addr, i = rd(data, 0)
    if i >= len(data):
        return addr, []
    tags, i = rd(data, i)
    args = []
    for t in tags[1:]:
        if t == "s":
            v, i = rd(data, i); args.append(v)
        elif t == "i":
            args.append(struct.unpack(">i", data[i:i+4])[0]); i += 4
        elif t == "f":
            args.append(struct.unpack(">f", data[i:i+4])[0]); i += 4
        elif t == "T":
            args.append(True)
        elif t == "F":
            args.append(False)
    return addr, args


class QLab:
    def __init__(self, host="127.0.0.1", port=53000, workspace=None, passcode=None):
        self.sock = socket.create_connection((host, port), timeout=5)
        self.sock.settimeout(0.6)
        self.ws = workspace
        if passcode is not None:
            # /connect MUST be unscoped. As /workspace/<id>/connect it returns
            # "ok:" with no permissions and everything after is denied.
            r = self.send("/connect", str(passcode), scoped=False, wait=1.0)
            if not r or "control" not in str(r):
                raise RuntimeError(f"OSC auth failed, got {r!r}")

    def send(self, addr, *args, wait=0.5, scoped=True):
        """Send an OSC message; return the parsed `data` from the reply, if any."""
        if scoped and self.ws and not addr.startswith("/workspace"):
            addr = f"/workspace/{self.ws}{addr}"
        self.sock.sendall(_slip_encode(build(addr, *args)))
        buf = b""
        t0 = time.time()
        while time.time() - t0 < wait:
            try:
                chunk = self.sock.recv(1 << 20)
            except socket.timeout:
                break
            if not chunk:
                break
            buf += chunk
            if buf.endswith(b"\xc0"):
                break
        for f in _slip_frames(buf):
            a, ar = parse(f)
            for x in ar:
                if isinstance(x, str) and x.strip().startswith("{"):
                    try:
                        r = json.loads(x)
                    except Exception:
                        continue
                    if r.get("status") != "ok":
                        raise RuntimeError(f"QLab {r.get('status')} for {addr}")
                    return r.get("data")
        return None

    def close(self):
        self.sock.close()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("address")
    ap.add_argument("args", nargs="*")
    ap.add_argument("--ws")
    ap.add_argument("--passcode")
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()
    q = QLab(host=a.host, workspace=a.ws, passcode=a.passcode)
    print(json.dumps(q.send(a.address, *a.args, scoped=bool(a.ws)),
                     ensure_ascii=False, indent=2))
