import { useMemo, useState } from 'react';
import { Scene } from './components/Review/Scene';
import { Header } from './components/UI/Header';
import { LibraryPanel } from './components/UI/LibraryPanel';
import { PropertiesPanel } from './components/UI/PropertiesPanel';
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
    <div className="flex flex-col h-screen overflow-hidden bg-gray-900 text-white">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <LibraryPanel />
        <div className="flex-1 relative">
          <Scene />
          <ControlsHelp />
        </div>
        <PropertiesPanel />
      </div>
    </div>
  );
}

export default App;
