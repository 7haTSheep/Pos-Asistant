import { useMemo, useState } from 'react';
import { Scene } from './components/Review/Scene';
import { Sidebar } from './components/UI/Sidebar';
import { ControlsHelp } from './components/UI/ControlsHelp';
import { ItemEditModal } from './components/UI/ItemEditModal';
import { Pencil, Eraser, MousePointer2, Ruler, Undo2, Redo2, Settings2 } from 'lucide-react';
import { useStore } from './store/store';
import './App.css';

function App() {
  const activeTool = useStore((state) => state.activeTool);
  const setActiveTool = useStore((state) => state.setActiveTool);
  const setMode = useStore((state) => state.setMode);
  const undo = useStore((state) => state.undo);
  const redo = useStore((state) => state.redo);
  const canUndo = useStore((state) => state.historyPast.length > 0);
  const canRedo = useStore((state) => state.historyFuture.length > 0);
  const selection = useStore((state) => state.selection);
  const objects = useStore((state) => state.objects);
  const updateObject = useStore((state) => state.updateObject);
  const removeObject = useStore((state) => state.removeObject);
  const [isItemModalOpen, setIsItemModalOpen] = useState(false);

  const selectedObject = useMemo(() => {
    if (!selection || selection.type !== 'object') return null;
    return objects.find((item) => item.id === selection.id) || null;
  }, [selection, objects]);

  return (
    <div className="app-shell">
      <header className="planner-topbar">
        <div className="topbar-left">
          <span className="brand-chip">FP</span>
          <span className="topbar-title">Warehouse Floor Planner</span>
        </div>
        <div className="topbar-actions">
          {selectedObject && (
            <button type="button" onClick={() => setIsItemModalOpen(true)}>Edit</button>
          )}
          {selectedObject && (
            <button
              type="button"
              onClick={() => {
                removeObject(selectedObject.id);
                setIsItemModalOpen(false);
              }}
            >
              Delete
            </button>
          )}
          <button type="button" onClick={undo} disabled={!canUndo}><Undo2 size={14} /> Undo</button>
          <button type="button" onClick={redo} disabled={!canRedo}><Redo2 size={14} /> Redo</button>
        </div>
      </header>

      <div className="planner-body">
        <aside className="tool-rail" aria-label="Editing tools">
          <button
            type="button"
            title="Pointer: select and move walls"
            className={activeTool === 'pointer' ? 'is-active' : ''}
            onClick={() => {
              setMode('edit');
              setActiveTool('pointer');
            }}
          >
            <MousePointer2 size={18} />
          </button>
          <button
            type="button"
            title="Pencil: draw walls"
            className={activeTool === 'pencil' ? 'is-active' : ''}
            onClick={() => {
              setMode('edit');
              setActiveTool('pencil');
            }}
          >
            <Pencil size={18} />
          </button>
          <button
            type="button"
            title="Eraser: delete walls under cursor"
            className={activeTool === 'eraser' ? 'is-active' : ''}
            onClick={() => {
              setMode('edit');
              setActiveTool('eraser');
            }}
          >
            <Eraser size={18} />
          </button>
          <button type="button" title="Measure"><Ruler size={18} /></button>
          <button type="button" title="Settings"><Settings2 size={18} /></button>
        </aside>

        <div className="scene-pane">
          <Scene />
        </div>

        <Sidebar />
      </div>

      <ControlsHelp />

      {isItemModalOpen && selectedObject && (
        <ItemEditModal
          item={selectedObject}
          onClose={() => setIsItemModalOpen(false)}
          onSave={(updates) => {
            updateObject(selectedObject.id, updates);
            setIsItemModalOpen(false);
          }}
          onDelete={() => {
            removeObject(selectedObject.id);
            setIsItemModalOpen(false);
          }}
        />
      )}
    </div>
  );
}

export default App;
