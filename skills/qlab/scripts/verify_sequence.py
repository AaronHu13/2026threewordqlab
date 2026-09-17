#!/usr/bin/env python3
"""Check that qlab_actN_sequence.json files match the cue lists of the FRONT QLab workspace.

usage: verify_sequence.py <qlab_actN_sequence.json> [...more json]
       verify_sequence.py --all <repo root>        # every Act */qlab_act*_sequence.json

For each json: dump the list named in it (dump_sequence.py, same folder as this script), normalise
both sides (sorted keys, "folder" ignored) and diff. Exit code 1 if any list differs or is missing.
Run it against the master workspace AND against each per-act workspace before committing.
"""
import glob, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
if args[:1] == ["--all"]:
    args = sorted(glob.glob(os.path.join(args[1], "Act *", "qlab_act*_sequence.json")))
if not args: sys.exit(__doc__)

def norm(cfg):
    # canonical form: every fade carries an explicit "secs", so json and dump agree even when they
    # picked different act-level fade_seconds defaults (dump uses the most common duration)
    cfg = dict(cfg); cfg.pop("folder", None); default = cfg.pop("fade_seconds", 2)
    seq = []
    for s in cfg["sequence"]:
        s = list(s)
        if s[0] == "fade":
            o = dict(s[2]) if len(s) > 2 else {}
            o["secs"] = float(o.get("secs", default)); s = s[:2] + [o]
        seq.append(s)
    cfg["sequence"] = seq
    return json.dumps(cfg, ensure_ascii=False, indent=1, sort_keys=True)

bad = 0
for jp in args:
    cfg = json.load(open(jp))
    folder = cfg["folder"] if os.path.isabs(cfg["folder"]) else os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(jp)), cfg["folder"]))
    tmp = os.path.join(tempfile.mkdtemp(), "dump.json")
    r = subprocess.run([sys.executable, os.path.join(HERE, "dump_sequence.py"), cfg["list"], cfg["prefix"], folder, tmp],
                       capture_output=True, text=True)
    label = os.path.relpath(jp)
    if r.returncode:
        err = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "dump failed"
        print(f"✗ {label}: {err}"); bad += 1; continue
    got = json.load(open(tmp))
    if norm(cfg) == norm(got):
        print(f"✓ {label}: {len(cfg['sequence'])} steps == QLab list {cfg['list']!r}")
    else:
        bad += 1
        print(f"✗ {label}: json ({len(cfg['sequence'])} steps) != QLab ({len(got['sequence'])} steps)")
        a, b = norm(cfg).splitlines(), norm(got).splitlines()
        import difflib
        for line in list(difflib.unified_diff(a, b, "json", "QLab", lineterm="", n=1))[:30]: print("   " + line)
    if r.stderr.strip(): print("   " + r.stderr.strip().replace("\n", "\n   "))
sys.exit(1 if bad else 0)
