-- Dump every media object on one slide of the front Keynote document.
-- usage: osascript media_info.applescript <slideNumber>
-- GIFs show up as class `movie`. `position` must be read as a record, not coerced to text.
on run argv
	set n to (item 1 of argv) as integer
	tell application "Keynote"
		set s to slide n of document 1
		set out to "slide " & n & " of " & (count of slides of document 1) & linefeed
		set out to out & "items: "
		repeat with it_ in iWork items of s
			set out to out & (class of it_ as text) & "; "
		end repeat
		set out to out & linefeed
		repeat with m in movies of s
			set out to out & "movie  | " & (file name of m as text) & " | rep=" & (repetition method of m as text) & " | vol=" & (movie volume of m) & linefeed
		end repeat
		repeat with a in audio clips of s
			set p to position of a
			set out to out & "audio  | " & (file name of a as text) & " | rep=" & (repetition method of a as text) & " | vol=" & (clip volume of a) & " | pos=" & (item 1 of p) & "," & (item 2 of p) & linefeed
		end repeat
		repeat with im in images of s
			set out to out & "image  | " & (file name of im as text) & linefeed
		end repeat
		return out
	end tell
end run
