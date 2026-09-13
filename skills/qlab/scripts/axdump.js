// Recursive accessibility dumper for a given app process (JXA).
// Use this instead of screencapture -- Screen Recording permission is not
// granted on these machines, so screenshots come back blank/blocked.
// usage: osascript -l JavaScript axdump.js "QLab" <maxDepth> [windowIndex]
function run(argv) {
  const app = argv[0] || "QLab";
  const maxDepth = parseInt(argv[1] || "8", 10);
  const winIdx = parseInt(argv[2] || "1", 10);
  const se = Application("System Events");
  const proc = se.processes[app];
  const win = proc.windows[winIdx - 1];
  const out = [];

  function label(e) {
    const parts = [];
    for (const k of ["role", "name", "value", "description", "title"]) {
      try {
        let v = e[k]();
        if (v !== null && v !== undefined && v !== "") {
          v = String(v);
          if (v.length > 60) v = v.slice(0, 60) + "…";
          parts.push(k + "=" + v);
        }
      } catch (err) {}
    }
    return parts.join(" ");
  }

  function walk(e, depth, path) {
    if (depth > maxDepth) return;
    let kids = [];
    try { kids = e.uiElements(); } catch (err) { return; }
    for (let i = 0; i < kids.length; i++) {
      const k = kids[i];
      const p = path + "/" + (i + 1);
      out.push("  ".repeat(depth) + p + " " + label(k));
      walk(k, depth + 1, p);
    }
  }

  out.push("WINDOW: " + label(win));
  walk(win, 1, "");
  return out.join("\n");
}
