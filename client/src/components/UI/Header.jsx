import React from 'react';
import { Save, FolderOpen, Download, LayoutTemplate, Settings, MousePointer2, Pencil, Eraser, Edit2, Eye } from 'lucide-react';
import { useStore } from '../../store/store';

export const Header = () => {
    const mode = useStore((state) => state.mode);
    const setMode = useStore((state) => state.setMode);
    const activeTool = useStore((state) => state.activeTool);
    const setActiveTool = useStore((state) => state.setActiveTool);

    return (
        <header className="h-14 bg-gray-800 border-b border-gray-700 flex items-center justify-between px-4 z-20">
            <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                        <LayoutTemplate className="text-white" size={20} />
                    </div>
                    <span className="font-bold text-white text-lg">Warehouse Designer</span>
                </div>

                <div className="h-6 w-px bg-gray-600 mx-2" />

                {/* Mode Toggle */}
                <div className="flex bg-gray-700 rounded-lg p-1">
                    <button
                        onClick={() => setMode('edit')}
                        className={`px-3 py-1 text-xs font-medium rounded transition-all flex items-center gap-1 ${mode === 'edit' ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-400 hover:text-white'}`}
                    >
                        <Edit2 size={14} />
                        Edit
                    </button>
                    <button
                        onClick={() => setMode('view')}
                        className={`px-3 py-1 text-xs font-medium rounded transition-all flex items-center gap-1 ${mode === 'view' ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-400 hover:text-white'}`}
                    >
                        <Eye size={14} />
                        View
                    </button>
                </div>

                <div className="h-6 w-px bg-gray-600 mx-2" />

                {/* Tool Selection */}
                <div className="flex bg-gray-700 rounded-lg p-1">
                    <button
                        onClick={() => setActiveTool('pointer')}
                        className={`p-1.5 rounded transition-all ${activeTool === 'pointer' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
                        title="Pointer (P)"
                    >
                        <MousePointer2 size={16} />
                    </button>
                    <button
                        onClick={() => setActiveTool('pencil')}
                        className={`p-1.5 rounded transition-all ${activeTool === 'pencil' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
                        title="Draw Walls (W)"
                    >
                        <Pencil size={16} />
                    </button>
                    <button
                        onClick={() => setActiveTool('eraser')}
                        className={`p-1.5 rounded transition-all ${activeTool === 'eraser' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
                        title="Erase Walls (E)"
                    >
                        <Eraser size={16} />
                    </button>
                </div>
            </div>

            <div className="flex items-center gap-2">
                <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition" title="Load">
                    <FolderOpen size={18} />
                </button>
                <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition" title="Save">
                    <Save size={18} />
                </button>
                <div className="h-6 w-px bg-gray-600 mx-1" />
                <button className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition shadow-lg shadow-blue-900/20">
                    <Download size={16} />
                    <span>Export</span>
                </button>
            </div>
        </header>
    );
};
