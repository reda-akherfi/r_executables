#Requires AutoHotkey v2.0
#SingleInstance Force

; Using Win+Ctrl+A as the hotkey
^#a:: {
    try {
        ; Save current clipboard contents
        originalClipboard := ClipboardAll()
        
        ; Paste operation might need to wait for clipboard to stabilize
        ClipWait(0.5)
        
        ; Send Select All (Ctrl+A) then Paste (Ctrl+V)
        Send('^a')
        Sleep(50) ; Brief pause for reliability
        Send('^v')
        
        ; Provide visual feedback
        FlashScreen()
    } catch as e {
        ; Error handling
        MsgBox("An error occurred: " e.Message, "Error", "Icon!")
        ; Restore original clipboard if possible
        try ClipboardAll(originalClipboard)
    }
}

; Rest of the script remains the same...
FlashScreen() {
    flashGui := Gui("+AlwaysOnTop -Caption +ToolWindow +LastFound")
    flashGui.BackColor := "EEAA99"
    WinSetTransparent(150, flashGui)
    
    screenWidth := A_ScreenWidth
    screenHeight := A_ScreenHeight
    
    flashGui.Show("NA x0 y0 w" screenWidth " h" screenHeight)
    
    loop 3 {
        WinSetTransparent(150 - (A_Index * 50), flashGui)
        Sleep(30)
    }
    
    flashGui.Destroy()
}