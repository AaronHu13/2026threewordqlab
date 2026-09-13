// Click a QLab cue-inspector tab by description, then dump that pane's AX tree.
// The cue inspector lives at window[0].uiElements[0].uiElements[2] in QLab 5.6.3.
// usage: osascript -l JavaScript tabdump.js "Time & Loops"
//        tabs: Basics / Triggers / Levels / Audio / Time & Loops / Trim / ...
function run(argv) {
  const tabName = argv[0] || "Time & Loops";
  const se = Application("System Events");
  const proc = se.processes["QLab"];
  const win = proc.windows[0];
  const insp = win.uiElements[0].uiElements[2]; // /1/3 = cue inspector

  // find and press the tab button
  const kids = insp.uiElements();
  for (const k of kids) {
    let d = "";
    try { d = String(k.description()); } catch (e) { continue; }
    if (d === tabName || d === tabName + ", selected") {
      k.actions["AXPress"].perform();
      break;
    }
  }
  delay(1.5);

  const out = [];
  function label(e) {
    const parts = [];
    for (const key of ["role", "name", "value", "description"]) {
      try {
        let v = e[key]();
        if (v !== null && v !== undefined && v !== "") {
          v = String(v);
          if (v.length > 70) v = v.slice(0, 70) + "…";
          parts.push(key + "=" + v);
        }
      } catch (err) {}
    }
    return parts.join(" ");
  }
  function walk(e, depth, path) {
    if (depth > 5) return;
    let ks = [];
    try { ks = e.uiElements(); } catch (err) { return; }
    for (let i = 0; i < ks.length; i++) {
      out.push("  ".repeat(depth) + path + "/" + (i + 1) + " " + label(ks[i]));
      walk(ks[i], depth + 1, path + "/" + (i + 1));
    }
  }
  walk(insp, 0, "");
  return out.join("\n");
}
