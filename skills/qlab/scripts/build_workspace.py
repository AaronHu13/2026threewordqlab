#!/usr/bin/env python3
"""Template: build a QLab 5 workspace from a folder of audio files.

Pattern it encodes (from the Act 6 show, 26 cues):
  * cue files are named `Cue<N>：<label>.mp3` -- N drives the running order
  * each audio cue is followed by its own 1s Fade-out cue (`<N>F`)
  * everything is do_not_continue, i.e. the operator hits GO for each step

TO USE: point FOLDER at the show folder, then edit main() to match the actual
running order. Open the target workspace in QLab first -- this writes into
`front workspace` and starts by DELETING every cue in it.

Why it drives the UI: `make new cue` is commented out of QLab.sdef, so the only
way to create a cue is clicking the Cues menu. The new cue lands after the
current selection and becomes selected, hence the select(last) dance.
"""
import os, re, subprocess

FOLDER = "/path/to/show folder"
FADE_SECONDS = 1.0


def osa(script):
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout.strip()


def cue_files():
    fs = [f for f in os.listdir(FOLDER) if f.lower().endswith((".mp3", ".wav", ".aif", ".aiff", ".m4a"))]
    def num(f):
        m = re.match(r"Cue\s*(\d+)", f, re.I)
        return int(m.group(1)) if m else 999
    return {num(f): f for f in sorted(fs, key=num)}


def clear_all():
    osa('tell application "QLab" to tell front workspace to delete every cue of first cue list')


def select(uid):
    osa(f'tell application "QLab" to tell front workspace to '
        f'set selected to {{cue id "{uid}" of first cue list}}')


def new_cue(kind):
    """Create a cue via the Cues menu; returns its uniqueID."""
    osa('tell application "QLab" to activate')
    osa(f'tell application "System Events" to tell process "QLab" to '
        f'click menu item "{kind}" of menu 1 of menu bar item "Cues" of menu bar 1')
    return osa('tell application "QLab" to tell front workspace to '
               'get uniqueID of item 1 of (selected as list)')


def make_audio(path, number, name, loop=False):
    uid = new_cue("Audio")
    p = path.replace('"', '\\"')
    osa(f'''tell application "QLab" to tell front workspace
      set c to cue id "{uid}" of first cue list
      set file target of c to (POSIX file "{p}")
      set q number of c to "{number}"
      set q name of c to "{name}"
      set continue mode of c to do_not_continue
      {"set infinite loop of c to true" if loop else ""}
    end tell''')
    return uid


def make_fade(target_uid, number, name, seconds=FADE_SECONDS):
    """A separate Fade cue -- the cue's own Integrated fade has no settable
    length (see references/scripting.md), and never fires at all on a loop."""
    uid = new_cue("Fade")
    osa(f'''tell application "QLab" to tell front workspace
      set f to cue id "{uid}" of first cue list
      set cue target of f to cue id "{target_uid}" of first cue list
      set duration of f to {seconds}
      set stop target when done of f to true
      set q number of f to "{number}"
      set q name of f to "{name}"
      set continue mode of f to do_not_continue
      setLevel f row 0 column 0 db -120.0
    end tell''')
    return uid


def main():
    files = cue_files()
    print("Clearing workspace...")
    clear_all()

    ids = {}
    last = None

    def add_audio(n, loop=False):
        nonlocal last
        if last:
            select(last)
        f = files[n]
        label = re.sub(r"^Cue\s*\d+[：:]?\s*", "", f).rsplit(".", 1)[0].strip()
        uid = make_audio(os.path.join(FOLDER, f), str(n),
                         f"Cue{n} {label}" + (" (loop)" if loop else ""), loop=loop)
        ids[n] = uid
        last = uid
        print(f"  audio Cue{n}: {label}" + (" [loop]" if loop else ""))

    def add_fade(n):
        nonlocal last
        if last:
            select(last)
        last = make_fade(ids[n], f"{n}F", f"Fade out Cue{n} ({FADE_SECONDS:g}s)")
        print(f"  fade  Cue{n}F -> {FADE_SECONDS:g}s fade out")

    # --- EDIT BELOW: the running order ---------------------------------
    # plain pattern: audio then its own fade out
    for n in sorted(k for k in files if k != 999):
        add_audio(n)
        add_fade(n)

    # overlap example: 11 loops under 12, then each fades on its own GO
    #   add_audio(11, loop=True); add_audio(12); add_fade(11); add_fade(12)
    # -------------------------------------------------------------------

    total = osa('tell application "QLab" to tell front workspace to '
                'get count of cues of first cue list')
    print(f"\nTotal cues: {total}")
    print('Save with: osascript -e \'tell application "QLab" to '
          'save document 1 in POSIX file "/path/x.qlab5"\'')


if __name__ == "__main__":
    main()
