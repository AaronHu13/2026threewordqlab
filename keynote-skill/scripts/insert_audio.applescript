-- Insert an audio file onto a slide via Insert > Choose... (the only way that works;
-- `make new audio clip` deadlocks Keynote). Verifies by counting audio clips.
-- usage: osascript insert_audio.applescript <slideNumber> </abs/path/to/audio.wav>
-- After this, "Start audio on click" is still CHECKED by default -> use click.js on
-- the Format > Audio inspector to uncheck it if the sound must autoplay.
on run argv
	set n to (item 1 of argv) as integer
	set audioPath to item 2 of argv
	tell application "Keynote"
		set theDoc to document 1
		set current slide of theDoc to slide n of theDoc
		set nBefore to count of audio clips of slide n of theDoc
		activate
	end tell
	delay 1.5
	tell application "System Events"
		tell process "Keynote"
			set frontmost to true
			delay 0.5
			if not frontmost then return "ABORT: Keynote not frontmost"
			-- Insert menu is menu bar item 5; item is "Choose..." (plain periods)
			click menu item "Choose..." of menu 1 of menu bar item 5 of menu bar 1
			delay 2.5
			keystroke "g" using {command down, shift down}
			delay 1.5
			keystroke audioPath
			delay 1
			keystroke return
			delay 3
		end tell
	end tell
	tell application "Keynote"
		set nAfter to count of audio clips of slide n of document 1
	end tell
	tell application "System Events" to tell process "Keynote" to set sheetOpen to (count of sheets of window 1) > 0
	if nAfter > nBefore then return "OK: inserted, slide " & n & " now has " & nAfter & " audio clip(s)"
	if sheetOpen then return "PENDING: file selected but Open panel still open (Return went into rename mode). Press Escape once, then click the Insert button with click.js."
	return "FAIL: no audio clip added and no panel open"
end run
