// Open QLab Workspace Settings -> Network -> OSC Access and dump the pane.
// Read the 4-digit passcode from here instead of hardcoding it; it is
// per-workspace. Do NOT flip the "No Passcode" row on without asking.
// usage: osascript -l JavaScript oscaccess.js
function run(argv) {
  const se = Application("System Events");
  const qlab = Application("QLab");
  qlab.activate();
  delay(0.6);
  const proc = se.processes["QLab"];

  // open settings if not already open
  let win = null;
  for (const w of proc.windows()) {
    if (String(w.name()).indexOf("Settings") !== -1) { win = w; break; }
  }
  if (!win) {
    se.keystroke(",", { using: ["command down"] });
    delay(2.5);
    for (const w of proc.windows()) {
      if (String(w.name()).indexOf("Settings") !== -1) { win = w; break; }
    }
  }
  if (!win) return "no settings window";

  const out = ["window=" + win.name()];

  // select the Network row in the sidebar
  try {
    const table = win.scrollAreas[0].tables[0];
    for (const r of table.rows()) {
      const t = r.uiElements[0].staticTexts[0].value();
      if (String(t) === "Network") { r.selected = true; break; }
    }
  } catch (e) { out.push("sidebar err: " + e); }
  delay(1.5);

  // press the OSC Access button
  let pressed = false;
  for (const b of win.buttons()) {
    let txt = "";
    try { txt = String(b.staticTexts[0].value()); } catch (e) {}
    if (txt === "OSC Access") {
      b.actions["AXPress"].perform();
      pressed = true;
      out.push("pressed OSC Access");
      break;
    }
  }
  if (!pressed) out.push("OSC Access button not found");
  delay(2);

  function label(e) {
    const parts = [];
    for (const k of ["role", "name", "value", "description"]) {
      try {
        let v = e[k]();
        if (v !== null && v !== undefined && v !== "") {
          v = String(v);
          if (v.length > 70) v = v.slice(0, 70) + "…";
          parts.push(k + "=" + v);
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
  walk(win, 0, "");
  return out.join("\n");
}
