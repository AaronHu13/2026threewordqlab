#!/usr/bin/env python3
"""Export one cue list of the front QLab workspace as a build_act_into_list.py sequence json.

usage: dump_sequence.py "<cue list q name>" <prefix> <audio folder> [out.json]

This is the inverse of build_act_into_list.py. Run it after an act's cues are final (built by
script OR edited by hand in the per-act workspace) so the act folder always carries a
qlab_actN_sequence.json that can rebuild the same list inside the festival-level workspace.

Mapping (q number = <prefix><N><suffix>):
  Audio            -> ["audio", N, {name, notes, cont?}]
  Fade             -> ["fade", N_of_target, {secs, cont, suffix, name, notes}]
  Start/Stop/Pause -> ["start"/"stop"/"pause", N_of_target, {cont, suffix, name, notes}]
  Memo             -> ["memo", N, {suffix, name, notes}]          (N parsed from its own q number)
Audio cue names equal to the file basename are omitted (the builder regenerates them). Only
non-default values are written so the json stays readable.
"""
import json, os, re, subprocess, sys

LIST, PREFIX, FOLDER = sys.argv[1], sys.argv[2], sys.argv[3]
OUT = sys.argv[4] if len(sys.argv) > 4 else None
SEP = "\x1f"

def osa(s):
    r = subprocess.run(["osascript", "-e", f'with timeout of 120 seconds\ntell application "QLab" to tell front workspace\n{s}\nend tell\nend timeout'],
                       capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stderr.strip())
    return r.stdout.rstrip("\n")
def esc(s): return s.replace('\\', '\\\\').replace('"', '\\"')

raw = osa(f'''set cl to first cue list whose q name is "{esc(LIST)}"
  set out to ""
  repeat with c in (get cues of cl)
    set t to q type of c
    set tgt to ""
    set dur to ""
    set cont to continue mode of c as text
    set nt to ""
    try
      set nt to notes of c
    end try
    if t is "Audio" then
      try
        set tgt to POSIX path of (file target of c as alias)
      end try
    else if t is in {{"Fade", "Start", "Stop", "Pause"}} then
      try
        set tgt to q number of (cue target of c)
      end try
      if t is "Fade" then set dur to duration of c as text
    end if
    set out to out & t & "{SEP}" & (q number of c) & "{SEP}" & (q name of c) & "{SEP}" & cont & "{SEP}" & tgt & "{SEP}" & dur & "{SEP}" & nt & linefeed
  end repeat
  return out''')

num_re = re.compile(rf"^{re.escape(PREFIX)}(\d+)([A-Za-z]*\d*)$")
def split_num(q):
    m = num_re.match(q)
    if not m: raise SystemExit(f"q number {q!r} does not match prefix {PREFIX!r}<N><suffix>")
    return int(m.group(1)), m.group(2)

seq, files = [], {}
for line in raw.split("\n"):
    if not line.strip(): continue
    t, q, name, cont, tgt, dur, notes = line.split(SEP)
    notes = notes.replace("\r", "\n")
    o = {}
    if t == "Audio":
        n, suf = split_num(q)
        base = os.path.splitext(os.path.basename(tgt))[0] if tgt else ""
        files[n] = os.path.basename(tgt)
        if name and name != base: o["name"] = name
        if cont != "do_not_continue": o["cont"] = cont
        if notes: o["notes"] = notes
        seq.append(["audio", n, o] if o else ["audio", n])
    elif t in ("Fade", "Start", "Stop", "Pause"):
        n, suf = split_num(q)
        if tgt:
            tn, _ = split_num(tgt)
            if tn != n: print(f"warn: {q} targets {tgt}, number mismatch; using target", file=sys.stderr); n = tn
        default_suf = {"Fade": "F", "Start": "R", "Stop": "S", "Pause": "P"}[t]
        if t == "Fade":
            secs = float(dur.replace(",", "."))
            o["secs"] = int(secs) if secs.is_integer() else secs
        if cont != "do_not_continue": o["cont"] = cont
        if suf != default_suf: o["suffix"] = suf
        if name and name != (f"Fade out {n} ({o.get('secs', 0):g}s)" if t == "Fade" else f"{ {'Start': 'Resume', 'Stop': 'Stop', 'Pause': 'Pause'}[t]} {n}"): o["name"] = name
        if notes: o["notes"] = notes
        seq.append([t.lower(), n, o])
    elif t == "Memo":
        n, suf = split_num(q)
        if suf != "M": o["suffix"] = suf
        if name: o["name"] = name
        if notes: o["notes"] = notes
        seq.append(["memo", n, o])
    else:
        print(f"warn: skipping unsupported cue type {t} #{q}", file=sys.stderr)

fades = [s[2].get("secs") for s in seq if s[0] == "fade"]
fade_default = max(set(fades), key=fades.count) if fades else 3
for s in seq:
    if s[0] == "fade" and s[2].get("secs") == fade_default: s[2].pop("secs")

missing = [f for f in files.values() if not os.path.exists(os.path.join(FOLDER, f))]
if missing: print(f"warn: {len(missing)} audio files not in {FOLDER}: {missing[:3]}…", file=sys.stderr)

cfg = {"folder": FOLDER, "list": LIST, "prefix": PREFIX, "fade_seconds": fade_default, "sequence": seq}
head = {k: v for k, v in cfg.items() if k != "sequence"}
lines = [json.dumps(s, ensure_ascii=False) for s in seq]          # one step per line, like the hand-written files
text = json.dumps(head, ensure_ascii=False, indent=2)[:-2] + ',\n  "sequence": [\n    ' + ",\n    ".join(lines) + "\n  ]\n}"
if OUT:
    open(OUT, "w", encoding="utf-8").write(text + "\n"); print(f"wrote {OUT}: {len(seq)} steps")
else:
    print(text)
