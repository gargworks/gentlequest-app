-- Nucleus Demo Screen Recording Helper (AppleScript)
-- 
-- This script helps automate QuickTime screen recording for demos.
-- It opens QuickTime, starts a screen recording, waits for the demo,
-- then stops and saves the recording.
--
-- Usage:
--   osascript scripts/record_demo_helper.scpt demo_a
--
-- Note: You'll need to manually grant screen recording permissions
-- to Terminal/Script Editor in System Preferences > Privacy & Security

on run argv
    -- Get demo ID from command line (e.g., "demo_a")
    if (count of argv) < 1 then
        display dialog "Usage: osascript record_demo_helper.scpt <demo_id>" buttons {"OK"} default button 1
        return
    end if
    
    set demoId to item 1 of argv
    set outputPath to (path to home folder as text) & "ai-mvp-backend:output:demos:" & demoId & "_screen.mov"
    
    -- Instructions for user
    display dialog "🎬 Nucleus Demo Recording Helper

Demo: " & demoId & "

Steps:
1. Click OK to open QuickTime
2. Start screen recording (File > New Screen Recording)
3. Perform your demo steps
4. Press ⌘+Control+Esc to stop recording
5. Save as: " & demoId & "_screen.mov

Ready?" buttons {"Cancel", "Start"} default button 2
    
    if button returned of result is "Cancel" then
        return
    end if
    
    -- Open QuickTime Player
    tell application "QuickTime Player"
        activate
        delay 1
        
        -- Note: AppleScript cannot programmatically start screen recording
        -- due to macOS security restrictions. User must manually:
        -- 1. File > New Screen Recording
        -- 2. Click record button
        -- 3. Perform demo
        -- 4. Stop recording (⌘+Control+Esc)
    end tell
    
    -- Show reminder
    display notification "Perform your demo, then press ⌘+Control+Esc to stop" with title "Recording in Progress"
    
end run
