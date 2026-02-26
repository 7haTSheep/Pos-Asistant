# Warehouse Viz 🏭

An interactive 3D warehouse floor layout visualizer. Design and manage your warehouse layout with drag-and-drop furniture placement, real-time editing, and keyboard shortcuts.

![React](https://img.shields.io/badge/React-19-blue?logo=react)
![Three.js](https://img.shields.io/badge/Three.js-r3f-black?logo=three.js)
![Vite](https://img.shields.io/badge/Vite-6-purple?logo=vite)

## ✨ Features

- **3D Warehouse Floor** — Interactive floor plane with grid overlay
- **Drag & Drop** — Click and drag furniture items to reposition them
- **Edit/View Modes** — Toggle between editing and viewing; camera is locked in edit mode
- **Keyboard Shortcuts** — Arrow keys, rotation, deletion, and fine movement
- **Resizable Items** — Adjust width, height, and depth of any object via sidebar controls
- **Multiple Object Types** — Shelves, fridges, and freezers with distinct styling
- **Controls Help Panel** — Press `?` to see all available shortcuts

## 🚀 Getting Started

```bash
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

## 🎮 Controls

### Mouse
| Action | Description |
|--------|-------------|
| **Click item** | Select object |
| **Click floor** | Deselect |
| **Click + Drag** | Move object (Edit mode) |
| **Right Drag** | Rotate camera (View mode) |
| **Scroll** | Zoom in/out |

### Keyboard (Edit Mode)
| Key | Action |
|-----|--------|
| `↑` `↓` `←` `→` | Move selected object (0.5 units) |
| `Shift` + Arrows | Fine move (0.1 units) |
| `R` | Rotate 90° |
| `Delete` | Remove object |
| `Escape` | Deselect |
| `?` | Toggle help panel |

## 🏗️ Architecture

```
warehouse_viz/
├── src/
│   ├── App.jsx                    # Main app layout
│   ├── store/
│   │   └── store.js               # Zustand state management
│   └── components/
│       ├── Review/
│       │   ├── Scene.jsx           # 3D scene, drag logic, shortcuts
│       │   ├── CameraController.jsx # OrbitControls wrapper
│       │   └── WarehouseFloor.jsx   # Floor plane with grid
│       ├── Objects/
│       │   └── Furniture.jsx       # Individual furniture items
│       └── UI/
│           ├── Sidebar.jsx         # Edit toggle, add objects, properties
│           └── ControlsHelp.jsx    # Keyboard shortcuts help panel
```

## 🛠️ Tech Stack

| Library | Purpose |
|---------|---------|
| **React 19** | UI framework |
| **Vite 6** | Build tool & dev server |
| **React Three Fiber** | React renderer for Three.js |
| **@react-three/drei** | Useful R3F helpers (OrbitControls, Html, etc.) |
| **Zustand** | Lightweight state management |
| **Three.js** | 3D rendering engine |
| **TailwindCSS 4** | Utility-first CSS |
| **Lucide React** | Icons |

## 📄 License

MIT
