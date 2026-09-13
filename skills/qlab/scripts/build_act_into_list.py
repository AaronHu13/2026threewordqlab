#!/usr/bin/env python3
"""Build one Act's cues into a named cue list of the front QLab workspace.

cfg json:
  {"folder": "/abs/audio/dir", "list": "Act 8:《…》", "prefix": "8_",
   "fade_seconds": 3,                       # default fade length
   "fades": {"11": 3}, "loops": [12],       # used only when no "sequence"
   "sequence": [                            # explicit steps, in cue-list order
     ["audio", 1],                          # Audio cue  -> q number <prefix>1
     ["audio", 1, {"name": "...", "notes": "..."}],
     ["fade", 2],                           # Fade out (default secs) -> <prefix>2F
     ["fade", 2, {"secs": 1, "cont": "auto_continue", "suffix": "F", "name": "...", "notes": "..."}],
     ["start", 37, {"cont": "do_not_continue", "name": "..."}],   # -> <prefix>37R
     ["stop", 37, {"cont": "auto_continue"}],                    # -> <prefix>37S
     ["pause", 37],                         # -> <prefix>37P  (needs a QLab license!)
     ["memo", 37, {"name": "...", "notes": "...", "suffix": "P"}] # -> <prefix>37P, does nothing on GO
   ]}

Files in `folder` are '<N>-label.ext' or 'Cue<N> label.ext'; N is the audio cue number.
New cues are appended after the last existing cue of the list. Existing (placeholder) cues
first get their q number blanked (otherwise QLab silently renumbers any colliding new cue),
and are deleted after the build. Free QLab 5: Pause/Script/Network/Devamp cues are broken.
"""
import os, re, subprocess, sys, json

cfg = json.load(open(sys.argv[1]))
FOLDER, LIST_NAME, PREFIX = cfg["folder"], cfg["list"], cfg["prefix"]
FADE_DEFAULT = cfg.get("fade_seconds", 1.0)
FADES = {int(k): v for k, v in cfg.get("fades", {}).items()}
LOOPS = set(cfg.get("loops", []))

def osa(s):
    r = subprocess.run(["osascript", "-e", s], capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stderr.strip() + "\n--- " + s)
    return r.stdout.strip()
def ws(b): return osa(f'tell application "QLab" to tell front workspace\n{b}\nend tell')
def esc(s): return s.replace('\\', '\\\\').replace('"', '\\"')

def files():
    out = {}
    for f in os.listdir(FOLDER):
        if not f.lower().endswith((".mp3",".wav",".aif",".aiff",".m4a",".flac")): continue
        m = re.match(r"^(?:Cue\s*)?(\d+)", f)
        if m:
            n = int(m.group(1))
            if n in out: raise SystemExit(f"two files share cue number {n}: {out[n]} / {f}")
            out[n] = f
    return out

def existing():
    return ws(f'''set cl to first cue list whose q name is "{LIST_NAME}"
      set out to ""
      repeat with c in (get cues of cl)
        set out to out & (uniqueID of c) & linefeed
      end repeat
      return out''').split()

def select(uid): ws(f'set selected to {{cue id "{uid}"}}')
def new_cue(kind):
    osa('tell application "QLab" to activate')
    osa(f'tell application "System Events" to tell process "QLab" to click menu item "{kind}" of menu 1 of menu bar item "Cues" of menu bar 1')
    return ws('get uniqueID of item 1 of (selected as list)')

def set_common(uid, number, name, cont, notes):
    ws(f'''set c to cue id "{uid}"
      set q number of c to "{esc(number)}"
      set q name of c to "{esc(name)}"
      set continue mode of c to {cont}
      {f'set notes of c to "{esc(notes)}"' if notes else ""}''')
    got = ws(f'get q number of cue id "{uid}"')
    if got != number: raise RuntimeError(f"q number collision: wanted {number}, QLab gave {got}")

def make_audio(n, fname, o):
    path = os.path.join(FOLDER, fname)
    name = o.get("name") or fname.rsplit(".",1)[0] + (" (loop)" if n in LOOPS else "")
    uid = new_cue("Audio")
    ws(f'''set c to cue id "{uid}"
      set file target of c to (POSIX file "{esc(path)}")
      {"set infinite loop of c to true" if n in LOOPS else ""}''')
    set_common(uid, f"{PREFIX}{n}", name, o.get("cont", "do_not_continue"), o.get("notes"))
    print(f"  audio {PREFIX}{n}: {name}"); return uid

def make_fade(n, target, o):
    secs = o.get("secs", FADES.get(n, FADE_DEFAULT)); cont = o.get("cont", "do_not_continue")
    number = f"{PREFIX}{n}{o.get('suffix', 'F')}"
    name = o.get("name") or f"Fade out {n} ({secs:g}s)"
    uid = new_cue("Fade")
    ws(f'''set f to cue id "{uid}"
      set cue target of f to cue id "{target}"
      set duration of f to {secs}
      set stop target when done of f to true
      setLevel f row 0 column 0 db -120.0''')
    set_common(uid, number, name, cont, o.get("notes"))
    print(f"  fade  {number} -> {n}, {secs:g}s [{cont}]"); return uid

CTRL = {"pause": ("Pause", "P", "Pause"), "start": ("Start", "R", "Resume"), "stop": ("Stop", "S", "Stop")}
def make_ctrl(kind, n, target, o):
    menu, suffix, label = CTRL[kind]
    cont = o.get("cont", "do_not_continue"); number = f"{PREFIX}{n}{o.get('suffix', suffix)}"
    uid = new_cue(menu)
    ws(f'set cue target of cue id "{uid}" to cue id "{target}"')
    set_common(uid, number, o.get("name") or f"{label} {n}", cont, o.get("notes"))
    print(f"  {kind:5} {number} -> {n} [{cont}]"); return uid

def make_memo(n, o):
    number = f"{PREFIX}{n}{o.get('suffix', 'M')}"
    uid = new_cue("Memo")
    set_common(uid, number, o.get("name") or f"Memo {n}", o.get("cont", "do_not_continue"), o.get("notes"))
    print(f"  memo  {number}: {o.get('name','')}"); return uid

def main():
    fs = files()
    seq = cfg.get("sequence")
    if not seq:
        seq = []
        for n in sorted(fs):
            seq.append(["audio", n])
            if n in FADES: seq.append(["fade", n, {"secs": FADES[n]}])
    ws(f'set current cue list to (first cue list whose q name is "{LIST_NAME}")')
    ph = existing()
    print(f"{len(ph)} existing cues to replace, {len(fs)} files, {len(seq)} steps")
    for pid in ph: ws(f'set q number of cue id "{pid}" to ""')   # avoid silent renumbering
    last, ids = ph[-1], {}
    for step in seq:
        kind, n = step[0], int(step[1])
        o = step[2] if len(step) > 2 and isinstance(step[2], dict) else {}
        if len(step) > 2 and not isinstance(step[2], dict):       # legacy: ["fade", n, secs] / ["stop", n, cont]
            o = {"secs": step[2]} if kind == "fade" else {"cont": step[2]}
        select(last)
        if kind == "audio":
            last = ids[n] = make_audio(n, fs[n], o)
        elif kind == "fade":
            last = make_fade(n, ids[n], o)
        elif kind == "memo":
            last = make_memo(n, o)
        else:
            last = make_ctrl(kind, n, ids[n], o)
    for pid in ph: ws(f'delete cue id "{pid}"')
    print("cues now:", ws(f'get count of cues of (first cue list whose q name is "{LIST_NAME}")'))
main()
