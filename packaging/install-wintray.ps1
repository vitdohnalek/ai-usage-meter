# Installs (or removes) the Windows tray for a WSL install of ai-usage-meter.
# Run from WSL with `make install-wintray`, which passes the two paths.
# Copies the package to %LOCALAPPDATA%\ai-usage-meter\app, makes sure pystray
# and Pillow are in the user's Python, writes the snapshot path to
# %APPDATA%\ai-usage-meter\wintray.json, adds a Startup shortcut and
# (re)starts the tray. Touches nothing inside the distro.
param(
    [string]$Source,
    [string]$SnapshotPath,
    [switch]$Uninstall
)
$ErrorActionPreference = 'Stop'

$Module   = 'ai_usage_meter.wintray.app'
$Home_    = Join-Path $env:LOCALAPPDATA 'ai-usage-meter'
$App      = Join-Path $Home_ 'app'
$Config   = Join-Path (Join-Path $env:APPDATA 'ai-usage-meter') 'wintray.json'
$Shortcut = Join-Path ([Environment]::GetFolderPath('Startup')) 'AI Usage Meter.lnk'

# Stop-Process returns before the process is gone, and a live tray keeps its
# working directory ($App) locked, so wait for the exit.
function Stop-Tray {
    Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe' OR Name = 'python.exe'" |
        Where-Object { $_.CommandLine -like "*$Module*" } |
        ForEach-Object {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            Wait-Process -Id $_.ProcessId -Timeout 10 -ErrorAction SilentlyContinue
        }
}

if ($Uninstall) {
    Stop-Tray
    Remove-Item -LiteralPath $Shortcut, $Config -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $Home_ -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $Home_) { throw "Could not remove $Home_ (still in use?)" }
    Write-Host 'Removed the Windows tray, its Startup shortcut, config and cached snapshot. pystray and Pillow stay installed.'
    exit 0
}

if (-not $Source -or -not $SnapshotPath) { throw 'Pass -Source <repo root> and -SnapshotPath <snapshot.json as Windows sees it>.' }
$Package = Join-Path $Source 'ai_usage_meter'
if (-not (Test-Path -LiteralPath $Package)) { throw "No ai_usage_meter package under $Source" }

if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw 'The Python launcher (py) is not on PATH: install Python for Windows from python.org.' }
$Python = "$(& py -3 -c 'import sys; print(sys.executable)')".Trim()
if (-not $Python) { throw 'py -3 found no Python 3.' }
$Pythonw = Join-Path (Split-Path $Python) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $Pythonw)) { throw "pythonw.exe not found next to $Python" }

# stderr is switched off inside Python: under Windows PowerShell 5.1 a
# traceback on stderr would end the script here instead of reaching pip.
& $Python -c 'import sys; sys.stderr = None; import pystray, PIL'
if ($LASTEXITCODE -ne 0) {
    & $Python -m pip install --user --disable-pip-version-check pystray Pillow
    if ($LASTEXITCODE -ne 0) { throw 'pip could not install pystray and Pillow' }
}

Stop-Tray
$New = "$App.new"
Remove-Item -LiteralPath $New -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $New -Force | Out-Null
Copy-Item -LiteralPath $Package -Destination $New -Recurse
Get-ChildItem -LiteralPath $New -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force
Remove-Item -LiteralPath $App -Recurse -Force -ErrorAction SilentlyContinue
if (Test-Path -LiteralPath $App) { throw "Could not replace $App (still in use?); the new copy is in $New" }
Rename-Item -LiteralPath $New -NewName (Split-Path $App -Leaf)

New-Item -ItemType Directory -Path (Split-Path $Config) -Force | Out-Null
$Json = @{ snapshot_path = $SnapshotPath } | ConvertTo-Json
[IO.File]::WriteAllText($Config, $Json, (New-Object Text.UTF8Encoding $false))

$Link = (New-Object -ComObject WScript.Shell).CreateShortcut($Shortcut)
$Link.TargetPath = $Pythonw
$Link.Arguments = "-m $Module"
$Link.WorkingDirectory = $App
$Link.Description = 'AI usage meter tray'
$Link.Save()

Start-Process -FilePath $Pythonw -ArgumentList '-m', $Module -WorkingDirectory $App
Write-Host "Tray launched; it also starts at login via $Shortcut"
Write-Host "Reading $SnapshotPath"
Write-Host 'If the icons sit in the overflow (^), drag them onto the taskbar, or turn Python on under'
Write-Host 'Settings > Personalization > Taskbar > Other system tray icons.'
