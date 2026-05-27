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

## 2. Audio Setup (AB13X USB Audio)

### Set ALSA default output to AB13X
```bash
# Find AB13X card number
aplay -l | grep AB13X
# Example output: card 1: Audio [AB13X USB Audio]

sudo tee /etc/asound.conf << 'EOF'
defaults.pcm.card 1
defaults.pcm.device 0
defaults.ctl.card 1
EOF
```

### Set react-carplay audio device
```bash
node -e "
const fs = require('fs');
const config = JSON.parse(fs.readFileSync('/home/fjiang/.config/react-carplay/config.json'));
config.audioDevice = 'AB13X USB Audio';
fs.writeFileSync('/home/fjiang/.config/react-carplay/config.json', JSON.stringify(config));
console.log('done');
"
```

> Note: AB13X card number may change on reboot. Run `aplay -l | grep AB13X` to verify.

---

## 3. react-carplay Build

### Clone
```bash
git clone https://github.com/rhysmorgan134/react-carplay.git
cd react-carplay
```

### Fix pcm-ringbuf-player (TypeScript 5.x incompatibility)
Node.js 20 ships with TypeScript 5.x which has stricter ArrayBuffer type checking.

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

### Build
```bash
npx electron-vite build
npx electron-rebuild -f -w socketcan
npx electron-builder --linux --arm64
```

Built app: `dist/linux-arm64-unpacked/react-carplay`

### Set display resolution and audio in config
```bash
node -e "
const fs = require('fs');
const config = JSON.parse(fs.readFileSync('/home/fjiang/.config/react-carplay/config.json'));
config.width = 1920;
config.height = 1080;
config.fps = 30;
config.dpi = 160;
config.audioDevice = 'AB13X USB Audio';
fs.writeFileSync('/home/fjiang/.config/react-carplay/config.json', JSON.stringify(config));
console.log('done');
"
```

---

## 4. Start Script
```bash
cat > ~/start-carplay.sh << 'EOF'
#!/bin/bash
export DISPLAY=:0
export HOME=/home/fjiang

# Set AB13X as default audio output
sleep 3
SINK_ID=$(wpctl status | grep "AB13X USB Audio Analog Stereo" | grep -v "Source" | awk '{print $2}' | tr -d '.' | head -1)
if [ -n "$SINK_ID" ]; then
    wpctl set-default $SINK_ID
    wpctl set-volume $SINK_ID 0.8
fi

/home/fjiang/react-carplay/dist/linux-arm64-unpacked/react-carplay \
  --no-sandbox \
  --remote-debugging-port=9222 \
  --remote-allow-origins=http://localhost:9222
EOF
chmod +x ~/start-carplay.sh
```

---

## 5. Systemd Autostart
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

## 6. Remote Debugging
```bash
# SSH tunnel from dev machine:
ssh -L 9222:localhost:9222 fjiang@<pi-ip>

# Open Chrome: chrome://inspect -> Configure -> localhost:9222
```

---

## Notes
- react-carplay source: https://github.com/rhysmorgan134/react-carplay
- Auto Box connects via USB for initial pairing, then uses WiFi for wireless CarPlay
- AppImage build fails on Pi, use `dist/linux-arm64-unpacked/` instead
- AB13X card number changes on reboot, ALSA config uses card 1 (verify with `aplay -l`)
