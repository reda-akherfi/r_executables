# yt-mp3-cutter.ps1
$cueFile = "C:\Users\redaa\Documents\r_executables\cue.txt"


# === Helper Function: Normalize Timestamps ===
function Normalize-Timestamp {
    param ([string]$time)

    # Already in hh:mm:ss
    if ($time -match "^\d{1,2}:\d{2}:\d{2}$") { return $time }

    # mm:ss → 00:mm:ss
    if ($time -match "^\d{1,2}:\d{2}$") {
        return "00:" + $time
    }

    if ($time -notmatch '^\d{1,2}:\d{1,2}:\d{1,2}$') {
        throw "Invalid timestamp format: $time"
    }
    # Pad hours, minutes, and seconds to 2 digits
    $parts = $time -split ':'
    $hh = $parts[0].PadLeft(2, '0')
    $mm = $parts[1].PadLeft(2, '0')
    $ss = $parts[2].PadLeft(2, '0')
    $time = "$hh`:$mm`:$ss"
}

# === Setup ===
$downloadsFolder = Join-Path $env:USERPROFILE "Downloads"
$defaultOutputFolder = "F:\music\classical"

# === Step 1: Get YouTube link ===
$ytLink = Read-Host "Enter YouTube video link"
if ([string]::IsNullOrWhiteSpace($ytLink)) {
    Write-Host "No link entered. Exiting."
    exit
}

# === Step 2: Download best audio as MP3 ===
Write-Host "`nDownloading best audio and converting to MP3 in $downloadsFolder..."
& yt-dlp.exe `
    --extract-audio `
    --audio-format mp3 `
    --audio-quality 0 `
    -f bestaudio/best `
    -o "$downloadsFolder\%(title)s.%(ext)s" `
    "$ytLink"

# === Step 3: Locate downloaded MP3 ===
$downloadedFile = Get-ChildItem -Path $downloadsFolder -Filter *.mp3 | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $downloadedFile) {
    Write-Host "Could not find downloaded MP3 file."
    exit
}

$inputFile = $downloadedFile.FullName
$pieceName = [System.IO.Path]::GetFileNameWithoutExtension($inputFile)

# === Step 4: Ask whether to cut ===
$cutChoice = Read-Host "`nDo you want to cut this piece into parts? (yes/no)"
if ($cutChoice -ne "yes") {
    $destFolder = Read-Host "Enter destination folder (blank for F:\music\classical)"
    if ([string]::IsNullOrWhiteSpace($destFolder)) {
        $destFolder = $defaultOutputFolder
    }

    if (!(Test-Path -Path $destFolder)) {
        New-Item -ItemType Directory -Path $destFolder | Out-Null
    }

    $newPath = Join-Path $destFolder $downloadedFile.Name
    Move-Item -Path $inputFile -Destination $newPath -Force
    Write-Host "`nFile moved to: $newPath"
    exit
}

# === Step 5: Define output folder ===
$cutFolder = Read-Host "Enter folder for cut pieces (blank for F:\music\classical)"
if ([string]::IsNullOrWhiteSpace($cutFolder)) {
    $cutFolder = $defaultOutputFolder
}

$partFolder = Join-Path $cutFolder $pieceName
if (!(Test-Path -Path $partFolder)) {
    New-Item -ItemType Directory -Path $partFolder | Out-Null
}

# === Step 6: Cue file or manual ===
$useCue = Read-Host "`nDo you want to use a cue file? (yes/no)"
$parts = @()
$manual = $false
if ($useCue -eq "yes") {
    $defaultCuePath = "C:\Users\redaa\Documents\r_executables\cue.txt"
    $cuePathInput = Read-Host "Enter path to the cue file (or press Enter for default: $defaultCuePath)"
    
    # Use default path if user pressed Enter without typing anything
    if ([string]::IsNullOrWhiteSpace($cuePathInput)) {
        $cuePath = $defaultCuePath
    } else {
        $cuePath = $cuePathInput
    }
    
    if (!(Test-Path $cuePath)) {
        Write-Host "Cue file not found at: $cuePath. Falling back to manual input."
        $manual = $true
    } else {
        $cueLines = Get-Content $cuePath | Where-Object { $_ -match "\d{1,2}:\d{2}" }
        foreach ($line in $cueLines) {
            if ($line -match "(.+?)\s+(\d{1,2}:\d{2})$") {
                $name = $matches[1].Trim()
                $start = Normalize-Timestamp $matches[2].Trim()
                $parts += [PSCustomObject]@{
                    Name = $name
                    Start = $start
                }
            }
        }
        # === Infer end times, prompt for last ===
        for ($i = 0; $i -lt $parts.Count; $i++) {
            if ($i -lt $parts.Count - 1) {
                $parts[$i] | Add-Member -NotePropertyName End -NotePropertyValue $parts[$i+1].Start
            } else {
                $lastEnd = Read-Host "End time of last part [$($parts[$i].Name)] (hh:mm:ss to trim applause, or blank to go to end)"
                if (-not [string]::IsNullOrWhiteSpace($lastEnd)) {
                    try {
                        $parts[$i] | Add-Member -NotePropertyName End -NotePropertyValue (Normalize-Timestamp $lastEnd)
                    } catch {
                        Write-Host "Invalid time format. Using full duration."
                        $parts[$i] | Add-Member -NotePropertyName End -NotePropertyValue ""
                    }
                } else {
                    $parts[$i] | Add-Member -NotePropertyName End -NotePropertyValue ""
                }
            }
            $parts[$i] | Add-Member -NotePropertyName Part -NotePropertyValue ($i + 1)
        }
    }
} else {
    $manual = $true
}

# === Step 7: Manual input fallback ===
if ($manual) {
    $done = $false
    $partIndex = 1
    while (-not $done) {
        $start = Read-Host "Start time of part $partIndex (hh:mm:ss or mm:ss, blank to finish)"
        if ([string]::IsNullOrWhiteSpace($start)) { break }

        try { Normalize-Timestamp $start | Out-Null } catch {
            Write-Host "Invalid time format."
            continue
        }

        $end = Read-Host "End time of part $partIndex (hh:mm:ss or mm:ss)"
        try { Normalize-Timestamp $end | Out-Null } catch {
            Write-Host "Invalid time format."
            continue
        }

        $name = Read-Host "Name of part $partIndex"
        if ([string]::IsNullOrWhiteSpace($name)) { $name = "Part_$partIndex" }

        $parts += [PSCustomObject]@{
            Part = $partIndex
            Name = $name
            Start = (Normalize-Timestamp $start)
            End   = (Normalize-Timestamp $end)
        }
        $partIndex++
    }
}

# === Step 8: Confirm and display structure ===
Write-Host "`nPart structure:"
$parts | Format-Table Part, Name, Start, End

$confirm = Read-Host "`nPress [Enter] to proceed with cutting, or type 'exit' to cancel"
if ($confirm -eq "exit") { exit }

# === Step 9: Cut using ffmpeg ===
Write-Host "`nCutting parts..."
$counter = 1
$total = $parts.Count

foreach ($part in $parts) {
    $outputFile = Join-Path $partFolder "$($part.Part) - $($part.Name).mp3"
    $startTS = [TimeSpan]::Parse((Normalize-Timestamp $part.Start))

    if ([string]::IsNullOrWhiteSpace($part.End)) {
        $ffArgs = @("-hide_banner", "-loglevel", "error", "-i", "$inputFile", "-ss", "$startTS", "-c:a", "libmp3lame", "-b:a", "320k", "$outputFile")
    } else {
        $endTS = [TimeSpan]::Parse((Normalize-Timestamp $part.End))
        $lengthTS = $endTS - $startTS
        $ffArgs = @("-hide_banner", "-loglevel", "error", "-i", "$inputFile", "-ss", "$startTS", "-t", "$lengthTS", "-c:a", "libmp3lame", "-b:a", "320k", "$outputFile")
    }

    Write-Progress -Activity "Cutting parts..." -Status "[$counter / $total] $($part.Name)" -PercentComplete (($counter / $total) * 100)
    & ffmpeg @ffArgs
    Write-Host "Saved: $($part.Name)"
    $counter++
}

Write-Progress -Activity "Cutting parts..." -Completed
Write-Host "`nAll parts saved in: $partFolder"

# === Step 10: Option to delete original ===
$deleteOriginal = Read-Host "`nDo you want to delete the original full MP3 file? (yes/no)"
if ($deleteOriginal -eq "yes") {
    try {
        Remove-Item -Path $inputFile -Force
        Write-Host "Original file deleted: $inputFile"
    } catch {
        Write-Host "Failed to delete the file: $_"
    }
} else {
    Write-Host "Original file kept: $inputFile"
}
