#!/usr/bin/env python3
"""Split a multi-cue-list QLab workspace into one standalone .qlab5 per cue list.

usage: split_workspace.py <main.qlab5> <out_root> [regex-of-list-names]

For every cue list whose q name matches the regex (default: all), the main file is copied to
<out_root>/<folder>/<folder>.qlab5 (folder = "Act N_ 剧名" derived from "Act N:《剧名》", else the
list name with unsafe chars replaced), opened, every OTHER cue list is emptied and deleted, the
file is saved in place and closed. Close the main workspace first (front workspace is used).

Gotchas handled here (QLab 5.6.3):
- `delete <cue list>` always pops a "Permanently delete Cue List …?" confirm sheet — even for an
  empty list — which blocks the AppleEvent until it times out (-1712). A background thread clicks
  the "Delete" button of any AXDialog window of QLab while the script runs.
- Right after `open`, QLab may ignore AppleEvents for a few seconds (-1712); osa() retries.
- The saved copy gets a NEW workspace unique id, so it can be opened alongside the main file.
"""
import subprocess, os, re, sys, time, shutil, threading

MAIN, OUT = sys.argv[1], sys.argv[2]
PAT = re.compile(sys.argv[3]) if len(sys.argv) > 3 else None

CLICK = '''const p=Application("System Events").processes.byName("QLab");let n=0;
for(const w of p.windows()){try{if(w.subrole()!=="AXDialog")continue;
for(const b of w.buttons()){if(b.name()==="Delete"){b.click();n++;break;}}}catch(x){}}n'''
stop = False
def clicker():
    while not stop:
        subprocess.run(["osascript", "-l", "JavaScript", "-e", CLICK], capture_output=True, text=True)
        time.sleep(0.4)

def osa(s, tries=4):
    for i in range(tries):
        r = subprocess.run(["osascript", "-e", f"with timeout of 90 seconds\n{s}\nend timeout"], capture_output=True, text=True)
        if r.returncode == 0: return r.stdout.strip()
        if "-1712" in r.stderr and i < tries - 1: time.sleep(4); continue
        raise RuntimeError(r.stderr.strip())
def esc(s): return s.replace('\\', '\\\\').replace('"', '\\"')

def folder_for(name):
    m = re.match(r"(Act \d+):\s*《(.+)》", name)
    return f"{m.group(1)}_ {m.group(2)}" if m else re.sub(r'[/:《》"]+', "_", name).strip()

subprocess.run(["open", MAIN]); time.sleep(7)
names = osa('tell application "QLab" to tell front workspace to get q name of every cue list').split(", ")
osa('tell application "QLab" to close every document saving no'); time.sleep(1)
names = [n for n in names if not PAT or PAT.search(n)]
print(f"{len(names)} lists to split: {names}")

threading.Thread(target=clicker, daemon=True).start()
for name in names:
    folder = folder_for(name); d = os.path.join(OUT, folder); os.makedirs(d, exist_ok=True)
    target = os.path.join(d, folder + ".qlab5"); shutil.copy(MAIN, target)
    subprocess.run(["open", target]); time.sleep(7)
    osa(f'tell application "QLab" to tell front workspace to set current cue list to (first cue list whose q name is "{esc(name)}")')
    res = osa(f'''tell application "QLab" to tell front workspace
      set keepName to "{esc(name)}"
      set names to {{}}
      repeat with cl in (get cue lists)
        if (q name of cl) is not keepName then set end of names to (q name of cl)
      end repeat
      repeat with n in names
        set cl to (first cue list whose q name is n)
        delete every cue of cl
        delete cl
      end repeat
      set nb to 0
      repeat with c in (get cues of first cue list)
        if (broken of c) then set nb to nb + 1
      end repeat
      return ((count of cue lists) as text) & " list, cues=" & ((count of cues of first cue list) as text) & ", broken=" & (nb as text)
    end tell''')
    osa(f'tell application "QLab"\nsave document 1 in POSIX file "{esc(target)}"\nclose document 1 saving no\nend tell')
    time.sleep(1)
    shutil.rmtree(os.path.join(d, folder + " backups"), ignore_errors=True)   # QLab auto-backup dir
    print(f"{target}  ->  {res}")
stop = True
