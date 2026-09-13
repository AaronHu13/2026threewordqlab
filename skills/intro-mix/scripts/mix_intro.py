#!/usr/bin/env python3
"""Mix a shared BGM with one (or a folder of) spoken announcement track(s) into finished intro cues.

usage: mix_intro.py <bgm> <voice.m4a | folder of voices> <out.mp3 | out folder>
                    [--at 7.0] [--bgm-db -7] [--voice-db -1] [--thresh -30]

Recipe (reverse-engineered from 喜剧节 2025 intro1-updated.mp3, verified against it to ~1 dB):
  1. Find where the speaker actually starts: first 10 ms window whose RMS exceeds --thresh dBFS.
     Recorded announcements carry 2–3 s of room noise/silence in front; that is cut, not mixed.
     Keep 60 ms of pre-roll with a 30 ms fade-in so the first consonant is not clipped.
  2. Trim trailing silence the same way (keep 250 ms, 150 ms fade-out).
  3. BGM is lowered by --bgm-db for the whole track (no side-chain ducking; last year did not
     duck either). The voice is placed so speech starts exactly at --at seconds.
  4. Sum both, brick-wall limit at -1 dBTP, write 320 kbps mp3 (last year's deliverable format).
Output length always equals the BGM length. The script prints onset/offset, integrated
loudness and true peak of each result so all intros can be compared in one glance.
"""
import subprocess, sys, array, math, json, os, argparse

ap = argparse.ArgumentParser()
ap.add_argument("bgm"); ap.add_argument("voice"); ap.add_argument("out")
ap.add_argument("--at", type=float, default=7.0, help="second at which speech starts")
ap.add_argument("--bgm-db", type=float, default=-7.0)
ap.add_argument("--voice-db", type=float, default=-1.0)
ap.add_argument("--thresh", type=float, default=-30.0, help="dBFS RMS that counts as speech")
a = ap.parse_args()
SR, WIN, PRE, POST, FADE_IN, FADE_OUT = 48000, 0.01, 0.06, 0.25, 0.03, 0.15
EXT = (".m4a", ".mp3", ".wav", ".aif", ".aiff", ".flac")

def decode_mono(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = array.array("f"); x.frombytes(raw); return x

def rms_db(seg): return 20 * math.log10(math.sqrt(sum(v * v for v in seg) / len(seg)) + 1e-9)

def speech_bounds(x):
    n = int(WIN * SR); loud = [i for i in range(0, len(x) - n + 1, n) if rms_db(x[i:i + n]) > a.thresh]
    if not loud: raise SystemExit("no speech found above threshold")
    return loud[0] / SR, (loud[-1] + n) / SR

def mix(voice, out):
    x = decode_mono(voice)
    onset, offset = speech_bounds(x)
    start = max(0.0, onset - PRE); end = min(len(x) / SR, offset + POST)
    delay_ms = int(round((a.at - (onset - start)) * 1000))
    if delay_ms < 0: raise SystemExit(f"{voice}: --at {a.at} too small for pre-roll")
    fc = (f"[1:a]atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS,"
          f"afade=t=in:d={FADE_IN},afade=t=out:st={end - start - FADE_OUT:.3f}:d={FADE_OUT},"
          f"aformat=channel_layouts=stereo,volume={a.voice_db}dB,adelay={delay_ms}:all=1[v];"
          f"[0:a]aformat=channel_layouts=stereo,volume={a.bgm_db}dB[b];"
          f"[b][v]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.891:attack=5:release=50:level=false[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.bgm, "-i", voice, "-filter_complex", fc, "-map", "[out]",
                    "-ar", str(SR), "-c:a", "libmp3lame", "-b:a", "320k", out], check=True)
    st = subprocess.run(["ffmpeg", "-hide_banner", "-i", out, "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    j = json.loads(st[st.rindex("{"):st.rindex("}") + 1])
    print(f"{os.path.basename(out)}: speech {onset:.2f}→{offset:.2f}s in source ({offset - onset:.1f}s), "
          f"placed at {a.at:.2f}s | {j['input_i']} LUFS, peak {j['input_tp']} dBTP")

if os.path.isdir(a.voice):
    os.makedirs(a.out, exist_ok=True)
    for f in sorted(os.listdir(a.voice)):
        if f.lower().endswith(EXT) and os.path.abspath(os.path.join(a.voice, f)) != os.path.abspath(a.bgm):
            mix(os.path.join(a.voice, f), os.path.join(a.out, "报幕-" + os.path.splitext(f)[0] + ".mp3"))
else:
    mix(a.voice, a.out)
