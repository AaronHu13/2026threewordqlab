#!/usr/bin/env python3
"""Build one Act's cues into a named cue list of the front QLab workspace.

cfg json: {"folder", "list", "prefix", "fade_seconds": 3,
           "fades": {"11": 3}, "loops": [12],           # used when no "sequence"
           "sequence": [["audio",1],["fade",2],["pause",37],["start",37],["stop",37,"auto_continue"], ...]}
Files are '<N>-label.ext' or 'Cue<N> label.ext'. New cues go after the last existing
cue in the list; existing (placeholder) cues are deleted afterwards."""
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
        if m: out[int(m.group(1))] = f
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

def make_audio(n, fname):
    path = os.path.join(FOLDER, fname)
    name = fname.rsplit(".",1)[0] + (" (loop)" if n in LOOPS else "")
    uid = new_cue("Audio")
    ws(f'''set c to cue id "{uid}"
      set file target of c to (POSIX file "{esc(path)}")
      set q number of c to "{PREFIX}{n}"
      set q name of c to "{esc(name)}"
      set continue mode of c to do_not_continue
      {"set infinite loop of c to true" if n in LOOPS else ""}''')
    print(f"  audio {PREFIX}{n}: {name}"); return uid

def make_fade(n, target, secs):
    uid = new_cue("Fade")
    ws(f'''set f to cue id "{uid}"
      set cue target of f to cue id "{target}"
      set duration of f to {secs}
      set stop target when done of f to true
      set q number of f to "{PREFIX}{n}F"
      set q name of f to "Fade out {n} ({secs:g}s)"
      set continue mode of f to do_not_continue
      setLevel f row 0 column 0 db -120.0''')
    print(f"  fade  {PREFIX}{n}F -> {n}, {secs:g}s"); return uid

CTRL = {"pause": ("Pause", "P", "Pause"), "start": ("Start", "R", "Resume"), "stop": ("Stop", "S", "Stop")}
def make_ctrl(kind, n, target, cont="do_not_continue"):
    menu, suffix, label = CTRL[kind]
    uid = new_cue(menu)
    ws(f'''set c to cue id "{uid}"
      set cue target of c to cue id "{target}"
      set q number of c to "{PREFIX}{n}{suffix}"
      set q name of c to "{label} {n}"
      set continue mode of c to {cont}''')
    print(f"  {kind:5} {PREFIX}{n}{suffix} -> {n} [{cont}]"); return uid

def main():
    fs = files()
    seq = cfg.get("sequence")
    if not seq:
        seq = []
        for n in sorted(fs):
            seq.append(["audio", n])
            if n in FADES: seq.append(["fade", n, FADES[n]])
    ws(f'set current cue list to (first cue list whose q name is "{LIST_NAME}")')
    ph = existing()
    print(f"{len(ph)} existing cues to replace, {len(fs)} files, {len(seq)} steps")
    last, ids = ph[-1], {}
    for step in seq:
        kind, n = step[0], int(step[1])
        select(last)
        if kind == "audio":
            last = ids[n] = make_audio(n, fs[n])
        elif kind == "fade":
            last = make_fade(n, ids[n], step[2] if len(step) > 2 else FADE_DEFAULT)
        else:
            last = make_ctrl(kind, n, ids[n], step[2] if len(step) > 2 else "do_not_continue")
    for pid in ph: ws(f'delete cue id "{pid}"')
    print("cues now:", ws(f'get count of cues of (first cue list whose q name is "{LIST_NAME}")'))
main()
