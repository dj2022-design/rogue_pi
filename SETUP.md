# Rogue Pi - Car Head Unit Setup

Custom car head unit for 2013 Nissan Rogue, built on Raspberry Pi 4 using react-carplay.

## Hardware
- Raspberry Pi 4 (4GB+)
- Argon ONE case with SSD
- WingCool TouchScreen (1920x1080)
- AB13X USB Audio (AUX output to car stereo)
- Magic Communication Auto Box (wireless CarPlay dongle, ID: 1314:1520)

---

## 1. Base System Setup

### Install Node.js 20
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Install system dependencies
```bash
sudo apt-get install -y usbmuxd ideviceinstaller feh git
```

### CarPlay dongle USB permissions
```bash
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="1314", ATTR{idProduct}=="152*", MODE="0660", GROUP="plugdev"' | \
  sudo tee /etc/udev/rules.d/52-nodecarplay.rules

sudo usermod -aG plugdev $USER
sudo udevadm control --reload-rules
sudo udevadm trigger
sudo reboot
```

---

## 2. Performance Optimization

### Overclock Pi 4 to 2GHz
Add to `/boot/firmware/config.txt` under `[all]`:
```ini
# Performance optimization
gpu_mem=256
over_voltage=6
arm_freq=2000
gpu_freq=750
```

### Disable unused services
```bash
# Keep bluetooth enabled (needed for OBD)
sudo systemctl disable avahi-daemon
sudo systemctl disable cups 2>/dev/null
```

### Verify overclock after reboot
```bash
vcgencmd measure_clock arm   # should show ~2000000000
vcgencmd measure_temp        # should stay under 75°C
vcgencmd get_throttled       # 0x0 = no throttling
```

---

## 3. Audio Setup (AB13X USB Audio)

### Set ALSA default output to AB13X
```bash
# Find AB13X card number (may change on reboot)
aplay -l | grep AB13X
# Example output: card 1: Audio [AB13X USB Audio]

sudo tee /etc/asound.conf << 'EOF'
defaults.pcm.card 1
defaults.pcm.device 0
defaults.ctl.card 1
EOF
```

---

## 4. react-carplay Build

### Clone
```bash
git clone https://github.com/rhysmorgan134/react-carplay.git
cd react-carplay
```

### Fix pcm-ringbuf-player (TypeScript 5.x incompatibility)
```bash
git clone https://github.com/rhysmorgan134/pcm-ringbuf-player.git ~/pcm-ringbuf-player
cd ~/pcm-ringbuf-player

sed -i 's/private feedWorklet(data: Int16Array)/private feedWorklet(data: Int16Array<ArrayBufferLike>)/' src/PcmPlayer.ts
sed -i 's/this.rb.push(data)/this.rb.push(data as Int16Array<ArrayBuffer>)/' src/PcmPlayer.ts

npm install --ignore-scripts --legacy-peer-deps
npm run build
```

### Install dependencies
```bash
cd ~/react-carplay
npm install --legacy-peer-deps file:../pcm-ringbuf-player
npm install ringbuf.js --legacy-peer-deps
```

### Fix Linux incompatibility in src/main/index.ts
```bash
sed -i 's/  systemPreferences.askForMediaAccess("microphone")/  if (process.platform === "darwin") systemPreferences.askForMediaAccess("microphone")/' src/main/index.ts
```

### Remove snap from build targets (fails on arm64)
```bash
sed -i '/    - snap/d' ~/react-carplay/electron-builder.yml
sed -i '/    - deb/d' ~/react-carplay/electron-builder.yml
```

### Wallpaper background (replaces white loading screen)
```bash
cp ~/wallpaper/minion.png ~/react-carplay/src/renderer/public/minion.png

cat > ~/react-carplay/src/renderer/src/App.css << 'EOF'
.App {
    text-align: center;
}
html, body {
    margin: 0px;
    padding: 0px;
    width: 100%;
    height: 100%;
    background-color: #000;
    background-image: url('/minion.png');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}
#root {
    width: 100%;
    height: 100%;
}
.App-header {
    background-color: #282c34;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-size: calc(10px + 2vmin);
    color: white;
}
@media (prefers-color-scheme: dark) {
  body { background-color: #000; color: white; }
}
@media (prefers-color-scheme: light) {
  body { background-color: #000; color: white; }
}
EOF
```

### Build
```bash
npx electron-vite build
npx electron-rebuild -f -w socketcan
npx electron-builder --linux --arm64
```

Built app: `dist/linux-arm64-unpacked/react-carplay`

### react-carplay config
```bash
node -e "
const fs = require('fs');
const config = JSON.parse(fs.readFileSync('/home/fjiang/.config/react-carplay/config.json'));
config.width = 1280;
config.height = 720;
config.fps = 30;
config.dpi = 160;
config.audioDevice = 'AB13X USB Audio';
config.wifiType = '5ghz';
config.packetMax = 131072;
fs.writeFileSync('/home/fjiang/.config/react-carplay/config.json', JSON.stringify(config));
console.log('done');
"
```

---

## 5. Desktop Wallpaper
```bash
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/wallpaper.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Wallpaper
Exec=feh --bg-fill /home/fjiang/wallpaper/minion.png
EOF
```

---

## 6. Start Script
```bash
cat > ~/start-carplay.sh << 'EOF'
#!/bin/bash
export DISPLAY=:0
export HOME=/home/fjiang
feh --bg-fill /home/fjiang/wallpaper/minion.png &
/home/fjiang/react-carplay/dist/linux-arm64-unpacked/react-carplay --no-sandbox
EOF
chmod +x ~/start-carplay.sh
```

---

## 7. Systemd Autostart
```bash
sudo tee /etc/systemd/system/carplay.service << 'EOF'
[Unit]
Description=React CarPlay
After=graphical.target network.target
Wants=graphical.target

[Service]
User=fjiang
Environment=DISPLAY=:0
Environment=HOME=/home/fjiang
ExecStart=/home/fjiang/start-carplay.sh
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable carplay
sudo systemctl start carplay
```

---

## 8. Remote Debugging (optional)
```bash
# Add to start-carplay.sh flags:
# --remote-debugging-port=9222 --remote-allow-origins=http://localhost:9222

# SSH tunnel from dev machine:
ssh -L 9222:localhost:9222 fjiang@<pi-ip>

# Open Chrome: chrome://inspect -> Configure -> localhost:9222
```

---

## Notes
- react-carplay source: https://github.com/rhysmorgan134/react-carplay
- Auto Box connects via USB for initial pairing, then uses WiFi for wireless CarPlay
- AppImage build may fail on Pi, use `dist/linux-arm64-unpacked/` directly
- AB13X card number may change on reboot, verify with `aplay -l | grep AB13X`
- 1280x720 recommended over 1920x1080 for better performance on Pi 4
- gbm_wrapper errors in logs are normal on Pi 4, do not affect functionality
