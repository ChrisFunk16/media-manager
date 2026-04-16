# 📱 Handy Sync Setup

## Einmalige Einrichtung (Handy)

1. **Termux installieren** (Google Play Store)

2. **Termux öffnen und SSH einrichten:**
```bash
pkg install openssh rsync
passwd  # Passwort setzen (z.B. 1234)
sshd    # SSH Server starten
```

3. **IP & Username herausfinden:**
```bash
ifconfig | grep inet  # z.B. 192.168.1.50
whoami                # z.B. u0_a123
```

4. **Storage Permission geben:**
```bash
termux-setup-storage  # Erlaubt Zugriff auf /storage/
```

## Script Konfiguration

### Linux: `sync-to-phone.sh`
1. Datei editieren
2. Zeile 4-6 anpassen:
   - `PHONE_IP` → Deine Handy IP
   - `PHONE_USER` → Dein Termux User
   - `PHONE_PORT` → Meist `8022`

3. Ausführen:
```bash
./sync-to-phone.sh
```

### Windows: `sync-to-phone.ps1`
1. Datei editieren
2. Zeile 4-6 anpassen (gleiche Werte wie oben)

3. **rsync benötigt!** Eine dieser Optionen:
   - **WSL:** `wsl --install` (empfohlen)
   - **Git for Windows:** https://git-scm.com/download/win
   - **cwRsync:** https://itefix.net/cwrsync

4. Ausführen (PowerShell):
```powershell
.\sync-to-phone.ps1
```

## Was wird synchronisiert?

- Alle Bilder: `.jpg`, `.png`
- Alle GIFs: `.gif`
- Alle Videos: `.mp4`, `.webm`
- Nur **neue oder geänderte Files** (rsync ist smart!)

## Zielordner auf Handy

```
/storage/emulated/0/Media/
├── images/
├── gifs/
├── videos/
└── hypno/
```

Zugriff über Android File Manager → "Media" Ordner

## Troubleshooting

**Connection refused:**
- SSH Server in Termux gestartet? → `sshd`
- Gleiche WLAN? → Beide Geräte im selben Netzwerk
- Firewall? → Termux Port 8022 freigeben

**Permission denied:**
- Storage Permission gegeben? → `termux-setup-storage`
- Passwort richtig? → `passwd` (neu setzen)

**Rsync nicht gefunden (Windows):**
- WSL installieren: `wsl --install`
- Oder Git for Windows nutzen

## SSH Auto-Login (Optional)

Statt Passwort jedes Mal einzugeben → SSH Key:

**Linux/Mac:**
```bash
ssh-keygen -t rsa
ssh-copy-id -p 8022 u0_a123@192.168.1.50
```

**Windows:**
```powershell
ssh-keygen -t rsa
type $HOME\.ssh\id_rsa.pub | ssh -p 8022 u0_a123@192.168.1.50 "cat >> ~/.ssh/authorized_keys"
```

Danach: Sync ohne Passwort! 🚀
