# Live2D AI Panel (Asuna) + Vehicle Panel

Three-panel layout: full-width top metrics bar, CarPlay lower-left, Asuna AI lower-right.

## Dependencies

### npm packages
```bash
cd ~/react-carplay
npm install pixi.js@6 pixi-live2d-display --ignore-scripts --legacy-peer-deps
```

### Live2D JS files
Copy from local machine to Pi:
```bash
scp live2dcubismcore.min.js fjiang@<pi-ip>:~/react-carplay/src/renderer/public/
scp live2d.min.js fjiang@<pi-ip>:~/react-carplay/src/renderer/public/
```

### Asuna model files
```bash
BASE="https://model.zulma.id/assets/models/SAO/asuna/asuna_02"
LOCAL="/home/fjiang/react-carplay/src/renderer/public/models/asuna"

mkdir -p $LOCAL/moc/asuna_02.1024 $LOCAL/exp $LOCAL/mtn

curl -o $LOCAL/asuna_02.model.json "$BASE/asuna_02.model.json"
curl -o $LOCAL/moc/asuna_02.moc "$BASE/moc/asuna_02.moc"
curl -o $LOCAL/moc/asuna_02.1024/texture_00.png "$BASE/moc/asuna_02.1024/texture_00.png"
curl -o $LOCAL/moc/asuna_02.1024/texture_01.png "$BASE/moc/asuna_02.1024/texture_01.png"
curl -o $LOCAL/moc/asuna_02.1024/texture_02.png "$BASE/moc/asuna_02.1024/texture_02.png"
curl -o $LOCAL/moc/asuna_02.1024/texture_03.png "$BASE/moc/asuna_02.1024/texture_03.png"

for exp in F_FUN F_FUN_HANIKAMI F_FUN_MAX F_FUN_SMILE F_FUN_WARM F_NOMAL F_SAD F_SURPRISE F_ANGRY F_SLEEP; do
  curl -o $LOCAL/exp/$exp.exp.json "$BASE/exp/$exp.exp.json"
done

for mtn in I_FUN_W I_SAD I_SAD_S I_SAD_W I_SNEESE I_SURPRISE I_SURPRISE_S I_SURPRISE_W REPEAT_01 REPEAT_02 REPEAT_03 I_ANGRY I_ANGRY_S I_ANGRY_W I_FUN I_FUN_S IDLING IDLING_02 IDLING_03; do
  curl -o $LOCAL/mtn/$mtn.mtn "$BASE/mtn/$mtn.mtn"
done

curl -o $LOCAL/asuna_02.physics.json "$BASE/asuna_02.physics.json"
```

---

## Layout
┌─────────────────────────────────────────────┐
│         VehiclePanel (full width, 160px)     │  top: 0, zIndex: 2000
├──────────────────────────────┬──────────────┤
│                              │              │
│         CarPlay              │  AIPanel     │
│    (width - 280px)           │  (280px)     │
│    marginTop: 160px          │  top: 160px  │
│                              │              │
└──────────────────────────────┴──────────────┘

---

## Code Changes

### 1. src/renderer/src/components/AIPanel.tsx
New file - Live2D Asuna panel (right side, below VehiclePanel).
- Position: `top: 160, right: 0, width: 280, height: calc(100vh - 160px)`
- Model: Cubism 2 Asuna at `models/asuna/asuna_02.model.json`
- Model position: `x: -60, y: 90, scale: 0.2`
- Idle motion: random every 20s, paused on tap
- Tap sequence: 吃惊→吃惊→开心→开心→打喷嚏→生气→生气→生气, resets after 20s
- Eye gaze: random every 8s via `focusController.focus(x, y)`, resets after 2s

### 2. src/renderer/src/components/VehiclePanel.tsx
New file - full-width top metrics bar (static data, OBD integration pending).
- Position: `top: 0, left: 0, right: 0, height: 160px`, zIndex: 2000
- Shows: Speed (center large), RPM / Coolant / Fuel (left), Battery / Load / DTC (right)

### 3. src/renderer/src/App.tsx
```tsx
import AIPanel from './components/AIPanel'
import VehiclePanel from './components/VehiclePanel'

// Add after </Modal>:
<AIPanel />
<VehiclePanel />
```

### 4. src/renderer/src/components/Carplay.tsx
```tsx
const PANEL_WIDTH = 280
const TOP_HEIGHT = 160
const width = window.innerWidth - PANEL_WIDTH
const height = window.innerHeight - TOP_HEIGHT

// Main div style:
{ height: 'calc(100% - 160px)', touchAction: 'none', marginTop: TOP_HEIGHT }

// videoContainer style:
marginRight: PANEL_WIDTH,
```

### 5. src/renderer/index.html
```html
<script src="/live2dcubismcore.min.js"></script>
<script src="/live2d.min.js"></script>
```

### 6. electron-builder.yml
```yaml
asarUnpack:
  - out/renderer/models/**
  - out/renderer/live2d.min.js
  - out/renderer/live2dcubismcore.min.js
  - resources/**
```

---

## Notes
- Live2D model files NOT included in repo (copyright)
- live2d.min.js and live2dcubismcore.min.js NOT included (proprietary)
- Model uses Cubism 2 SDK via `pixi-live2d-display/cubism2`
- Eye gaze controlled via `model.internalModel.focusController.focus(x, y)`
- Asuna motions: 0=I_FUN_W, 4=I_SNEESE, 5=I_SURPRISE, 6=I_SURPRISE_S, 11=I_ANGRY, 14=I_FUN, 15=I_FUN_S
- OBD data integration pending (VehiclePanel currently shows static values)
