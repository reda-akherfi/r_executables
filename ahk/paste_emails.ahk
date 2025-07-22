#Requires AutoHotkey v2.0
#SingleInstance Force

; Hotkey to show email selection dialog (Win+Ctrl+E)
^#e::ShowEmailMenu()

ShowEmailMenu() {
    ; Create the GUI
    myGui := Gui(, "Select Email to Paste")
    myGui.OnEvent("Close", Gui_Close)
    myGui.SetFont("s10", "Segoe UI")
    
    ; Email options - Edit these as needed
    emails := [
        "akherfi3|redaakherfi3@gmail.com",
        "inpt|akherfi.reda@ine.inpt.ac.ma",
        "akherfi68|redaakherfi68@gmail.com",
        "akherfi07|redaakherfi07@gmail.com",
        "francophone|redafrancophone2017@gmail.com",
        "akherfi2011|akherfi2011@gmail.com"
    ]
    
    ; Add radio buttons
    myGui.Add("Text",, "Select email to paste:")
    rbArray := []
    Loop emails.Length {
        ; First radio gets the Group option
        options := (A_Index = 1) ? "vSelectedEmail Group Checked" : "yp"
        rbArray.Push(myGui.Add("Radio", options, StrSplit(emails[A_Index], "|")[1]))
    }
    
    ; Add buttons
    myGui.Add("Button", "Default w80", "OK").OnEvent("Click", (*) => PasteSelectedEmail(myGui, emails, rbArray))
    myGui.Add("Button", "x+10 w80", "Cancel").OnEvent("Click", Gui_Close)
    
    ; Show GUI
    myGui.Show("Center")
    
    Gui_Close(*) {
        myGui.Destroy()
    }
}

PasteSelectedEmail(GuiObj, emails, rbArray) {
    ; Find which radio button is selected
    selectedIndex := 0
    Loop rbArray.Length {
        if (rbArray[A_Index].Value) {
            selectedIndex := A_Index
            break
        }
    }
    
    if (selectedIndex > 0) {
        ; Get the corresponding email
        email := StrSplit(emails[selectedIndex], "|")[2]
        
        ; Close GUI first
        GuiObj.Destroy()
        
        ; Type the email directly
        SendText(email)
    }
    else {
        GuiObj.Destroy()
    }
}