// CGEvent-based clicker for Keynote (JXA).
// System Events' `click at {x,y}` is a silent no-op inside Keynote; this posts
// real mouse events instead. Coordinates are screen POINTS (Retina px / 2).
// Refuses to click when Keynote is not frontmost (user switched apps).
// usage: osascript -l JavaScript click.js x1 y1 [x2 y2 ...]   (1s between clicks)
ObjC.import('CoreGraphics');
function click(x, y) {
  const pt = {x: x, y: y};
  const move = $.CGEventCreateMouseEvent(null, $.kCGEventMouseMoved, pt, $.kCGMouseButtonLeft);
  $.CGEventPost($.kCGHIDEventTap, move);
  delay(0.15);
  const down = $.CGEventCreateMouseEvent(null, $.kCGEventLeftMouseDown, pt, $.kCGMouseButtonLeft);
  const up = $.CGEventCreateMouseEvent(null, $.kCGEventLeftMouseUp, pt, $.kCGMouseButtonLeft);
  $.CGEventPost($.kCGHIDEventTap, down);
  delay(0.08);
  $.CGEventPost($.kCGHIDEventTap, up);
}
function run(argv) {
  if (argv.length < 2) return 'usage: click.js x y [x y ...]';
  const app = Application('Keynote'); app.activate();
  delay(1.0);
  const se = Application('System Events');
  const proc = se.processes.byName('Keynote');
  proc.frontmost = true; delay(0.4);
  if (!proc.frontmost()) return 'not frontmost';
  for (let i = 0; i + 1 < argv.length; i += 2) {
    click(parseFloat(argv[i]), parseFloat(argv[i + 1]));
    delay(1.0);
  }
  return 'clicked ' + argv.join(',');
}
