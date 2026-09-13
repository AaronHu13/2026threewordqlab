-- Dump the controls of Keynote's front window (inspector tabs, checkboxes, popups, labels).
-- Use it to verify e.g. that "Start audio on click" is now 0 after clicking it.
-- `entire contents` is flaky in Keynote: if the output is empty, just run it again.
-- usage: osascript inspector_dump.applescript [tabNameToPressFirst]
on run argv
	set wanted to ""
	if (count of argv) > 0 then set wanted to item 1 of argv
	with timeout of 60 seconds
		tell application "System Events"
			tell process "Keynote"
				set els to entire contents of window 1
				if wanted is not "" then
					repeat with e in els
						try
							if role of e is "AXRadioButton" and (description of e) is wanted then
								perform action "AXPress" of e -- works even when Keynote is not frontmost
								exit repeat
							end if
						end try
					end repeat
					delay 1.2
					set els to entire contents of window 1
				end if
				set out to "elements=" & (count of els) & linefeed
				repeat with e in els
					try
						set r to role of e
						if r is in {"AXRadioButton", "AXCheckBox", "AXPopUpButton", "AXStaticText", "AXSlider"} then
							set t to ""
							try
								set t to (value of e) as text
							end try
							set d to ""
							try
								set d to (description of e) as text
							end try
							set out to out & r & " | " & d & " | " & t & linefeed
						end if
					end try
				end repeat
				return out
			end tell
		end tell
	end timeout
end run
