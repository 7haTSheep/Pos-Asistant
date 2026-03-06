import { useMemo, useState } from 'react';
import { Scene } from './components/Review/Scene';
import { Header } from './components/UI/Header';
import { LibraryPanel } from './components/UI/LibraryPanel';
import { PropertiesPanel } from './components/UI/PropertiesPanel';
import { ControlsHelp } from './components/UI/ControlsHelp';
import { ItemEditModal } from './components/UI/ItemEditModal';
import { LayoutManager } from './components/UI/LayoutManager';
import { Pencil, Eraser, MousePointer2, Ruler, Undo2, Redo2, Settings2, LayoutGrid } from 'lucide-react';
import { useStore } from './store/store';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
  const [showLayoutManager, setShowLayoutManager] = useState(false);

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
          
          {/* Layout Manager Toggle Button */}
          <button
            onClick={() => setShowLayoutManager(!showLayoutManager)}
            className={`absolute top-4 right-4 z-20 p-2 rounded-lg border transition-colors ${
              showLayoutManager 
                ? 'bg-blue-600 border-blue-500 text-white' 
                : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-white'
            }`}
            title="Layout Library"
          >
            <LayoutGrid size={20} />
          </button>
          
          {/* Layout Manager Panel */}
          {showLayoutManager && (
            <div className="absolute top-16 right-4 z-20 w-80 bg-gray-800 border border-gray-700 rounded-lg shadow-xl p-4">
              <LayoutManager apiUrl={API_URL} />
            </div>
          )}
        </div>
        <PropertiesPanel />
      </div>
      
      {/* Item Edit Modal */}
      {isItemModalOpen && selectedObject && (
        <ItemEditModal
          object={selectedObject}
          onClose={() => setIsItemModalOpen(false)}
          onUpdate={(updates) => {
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
