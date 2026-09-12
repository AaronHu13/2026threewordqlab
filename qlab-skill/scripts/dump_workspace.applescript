on run argv
  set wsName to item 1 of argv
  set out to ""
  tell application "QLab"
    set ws to workspace (wsName as integer)
    tell ws
      set out to out & "WORKSPACE: " & (get name) & "  id=" & (get unique id) & linefeed
      repeat with cl in (get cue lists)
        set out to out & "== CUELIST: " & (q name of cl) & " (" & (count of cues of cl) & " top-level cues)" & linefeed
        set out to out & my dumpCues(cues of cl, "  ")
      end repeat
    end tell
  end tell
  return out
end run

on dumpCues(cueList, indent)
  set out to ""
  tell application "QLab"
    repeat with c in cueList
      set t to q type of c
      set ln to indent & "[" & t & "] #" & (q number of c) & " | " & (q name of c) & " | id=" & (uniqueID of c)
      try
        set ln to ln & " | cont=" & (continue mode of c as text)
      end try
      try
        set ln to ln & " | pre=" & (pre wait of c) & " post=" & (post wait of c)
      end try
      if t is "Audio" then
        try
          set ln to ln & " | file=" & (POSIX path of (file target of c as alias))
        on error
          try
            set ln to ln & " | file=" & (file target of c as text)
          on error
            set ln to ln & " | file=?"
          end try
        end try
        try
          set ln to ln & " | dur=" & (duration of c) & " loop=" & (infinite loop of c)
        end try
      else if t is "Fade" then
        try
          set ln to ln & " | dur=" & (duration of c) & " target=" & (q number of (cue target of c)) & "/" & (q name of (cue target of c)) & " stopWhenDone=" & (stop target when done of c)
        on error errm
          set ln to ln & " | fade-err:" & errm
        end try
      else if t is in {"Start", "Stop", "Pause"} then
        try
          set ln to ln & " | target=" & (q number of (cue target of c)) & "/" & (q name of (cue target of c))
        end try
      else if t is "Group" then
        try
          set ln to ln & " | mode=" & (mode of c as text)
        end try
      end if
      set out to out & ln & linefeed
      if t is "Group" then
        set out to out & my dumpCues(cues of c, indent & "    ")
      end if
    end repeat
  end tell
  return out
end dumpCues
