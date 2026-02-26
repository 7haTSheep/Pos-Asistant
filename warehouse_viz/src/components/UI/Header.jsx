import React from 'react';
import { Save, FolderOpen, Download, LayoutTemplate, Settings } from 'lucide-react';
import { useStore } from '../../store/store';

export const Header = () => {
    const mode = useStore((state) => state.mode);
    const setMode = useStore((state) => state.setMode);

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

                <div className="flex bg-gray-700 rounded-lg p-1">
                    <button
                        className={`px-3 py-1 text-xs font-medium rounded transition-all ${mode !== '2d' ? 'bg-gray-600 text-gray-300' : 'bg-blue-600 text-white shadow-sm'}`}
                    // onClick={() => setView('2d')} // TODO: Implement 2D view
                    >
                        2D View
                    </button>
                    <button
                        className={`px-3 py-1 text-xs font-medium rounded transition-all ${mode !== '3d' ? 'bg-gray-600 text-gray-300' : 'bg-blue-600 text-white shadow-sm'}`}
                    // onClick={() => setView('3d')} // TODO: Implement 3D view
                    >
                        3D View
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
