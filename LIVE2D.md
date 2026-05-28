# Live2D AI Panel (Asuna)

Right-side panel featuring Live2D Asuna character with vehicle info display.

## Dependencies

### npm packages
```bash
cd ~/react-carplay
npm install pixi.js@6 pixi-live2d-display --ignore-scripts --legacy-peer-deps
```

### Live2D JS files
Copy from your local machine to Pi:
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

## Code Changes

### 1. src/renderer/src/components/AIPanel.tsx
New file - Live2D panel with vehicle info (upper) and Asuna character (lower).
See `patches/AIPanel.tsx` for full source.

### 2. src/renderer/src/App.tsx
```tsx
// Add import
import AIPanel from './components/AIPanel'

// Add component after </Modal>
<AIPanel />
```

### 3. src/renderer/src/components/Carplay.tsx
```tsx
// Reserve space for panel
const PANEL_WIDTH = 280
const width = window.innerWidth - PANEL_WIDTH

// Add marginRight to videoContainer style
marginRight: PANEL_WIDTH,
```

### 4. src/renderer/index.html
```html
<!-- Add before </body> -->
<script src="/live2dcubismcore.min.js"></script>
<script src="/live2d.min.js"></script>
```

### 5. electron-builder.yml
```yaml
asarUnpack:
  - out/renderer/models/**
  - out/renderer/live2d.min.js
  - out/renderer/live2dcubismcore.min.js
  - resources/**
```

---

## Notes
- Live2D model files are NOT included in repo (copyright)
- Download Asuna model from model.zulma.id
- live2d.min.js and live2dcubismcore.min.js are NOT included (proprietary)
- Model uses Cubism 2 SDK via pixi-live2d-display/cubism2
