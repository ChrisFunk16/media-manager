# Sync Media zu Handy (nur neue/geaenderte Files)
# Windows PowerShell Version

$PHONE_IP = "192.168.178.64"      # <-- Deine Handy IP hier
$PHONE_USER = "u0_a377"         # <-- Termux User (meist u0_aXXX)
$PHONE_PORT = "8022"            # Termux SSH Port

$LOCAL_DIR = "$env:USERPROFILE\media-manager\sorted\"
$PHONE_DIR = "/storage/emulated/0/Media/"

Write-Host "[*] Syncing to phone..." -ForegroundColor Cyan
Write-Host "    IP: $PHONE_IP" -ForegroundColor Gray
Write-Host ""

# Check if rsync exists (via WSL or installed)
$hasRsync = $false

# Try WSL rsync first
if (Get-Command wsl -ErrorAction SilentlyContinue) {
    Write-Host "[+] Using WSL rsync..." -ForegroundColor Green
    
    # Convert Windows path to WSL path
    $wslPath = $LOCAL_DIR -replace '\\', '/' -replace 'C:', '/mnt/c'
    
    wsl rsync -avz --progress `
        --include='*/' `
        --include='*.jpg' --include='*.png' --include='*.gif' `
        --include='*.mp4' --include='*.webm' `
        --exclude='*' `
        -e "ssh -p $PHONE_PORT" `
        "$wslPath" `
        "${PHONE_USER}@${PHONE_IP}:${PHONE_DIR}"
    
    $hasRsync = $true
}
# Try native rsync (cwRsync or Git Bash)
elseif (Get-Command rsync -ErrorAction SilentlyContinue) {
    Write-Host "[+] Using native rsync..." -ForegroundColor Green
    
    rsync -avz --progress `
        --include='*/' `
        --include='*.jpg' --include='*.png' --include='*.gif' `
        --include='*.mp4' --include='*.webm' `
        --exclude='*' `
        -e "ssh -p $PHONE_PORT" `
        "$LOCAL_DIR" `
        "${PHONE_USER}@${PHONE_IP}:${PHONE_DIR}"
    
    $hasRsync = $true
}
else {
    Write-Host "[!] rsync nicht gefunden!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Optionen:" -ForegroundColor Yellow
    Write-Host "  1. WSL installieren: wsl --install"
    Write-Host "  2. Git for Windows installieren (enthaelt rsync)"
    Write-Host "  3. cwRsync installieren: https://itefix.net/cwrsync"
    Write-Host ""
    exit 1
}

if ($hasRsync) {
    Write-Host ""
    Write-Host "[+] Sync done!" -ForegroundColor Green
}
