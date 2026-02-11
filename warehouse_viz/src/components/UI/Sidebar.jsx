import React from 'react';
import { useStore } from '../../store/store';
import { Box, Snowflake, Archive, Pencil, Eye } from 'lucide-react';

export const Sidebar = () => {
    const addObject = useStore((state) => state.addObject);
    const selection = useStore((state) => state.selection);
    const objects = useStore((state) => state.objects);
    const removeObject = useStore((state) => state.removeObject);
    const updateObject = useStore((state) => state.updateObject);
    const mode = useStore((state) => state.mode);
    const setMode = useStore((state) => state.setMode);

    const isEditMode = mode === 'edit';

    const selectedObject = selection?.type === 'object'
        ? objects.find(o => o.id === selection.id)
        : null;

    const toggleMode = () => {
        setMode(isEditMode ? 'view' : 'edit');
    };

    const formatCoord = (val) => typeof val === 'number' ? val.toFixed(1) : '—';

    return (
        <div className="absolute top-0 left-0 h-full w-64 bg-gray-800 text-white p-4 overflow-y-auto z-10 shadow-lg">
            <h1 className="text-xl font-bold mb-4">Warehouse Viz</h1>

            {/* Edit Mode Toggle */}
            <button
                onClick={toggleMode}
                className={`w-full mb-6 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg font-semibold text-sm transition-all ${isEditMode
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shadow-[0_0_12px_rgba(52,211,153,0.15)]'
                    : 'bg-gray-700 text-gray-300 border border-gray-600 hover:bg-gray-600'
                    }`}
            >
                {isEditMode ? <Pencil size={16} /> : <Eye size={16} />}
                {isEditMode ? 'Edit Mode' : 'View Mode'}
                <span className={`ml-auto w-2 h-2 rounded-full ${isEditMode ? 'bg-emerald-400 animate-pulse' : 'bg-gray-500'}`} />
            </button>

            {/* Add Object */}
            <div className={`mb-8 transition-opacity ${isEditMode ? 'opacity-100' : 'opacity-40 pointer-events-none'}`}>
                <h2 className="text-sm uppercase text-gray-400 mb-3 font-semibold">Add Object</h2>
                <div className="grid grid-cols-2 gap-2">
                    <button
                        onClick={() => addObject('shelf', [0, 1.5, 0])}
                        className="flex flex-col items-center justify-center p-3 bg-gray-700 hover:bg-gray-600 rounded transition"
                    >
                        <Archive size={24} className="mb-2 text-orange-400" />
                        <span className="text-xs">Shelf</span>
                    </button>

                    <button
                        onClick={() => addObject('fridge', [0, 1, 0])}
                        className="flex flex-col items-center justify-center p-3 bg-gray-700 hover:bg-gray-600 rounded transition"
                    >
                        <Snowflake size={24} className="mb-2 text-blue-300" />
                        <span className="text-xs">Fridge</span>
                    </button>

                    <button
                        onClick={() => addObject('freezer', [0, 0.5, 0])}
                        className="flex flex-col items-center justify-center p-3 bg-gray-700 hover:bg-gray-600 rounded transition"
                    >
                        <Box size={24} className="mb-2 text-cyan-200" />
                        <span className="text-xs">Freezer</span>
                    </button>
                </div>
            </div>

            {/* Selected Object Properties */}
            {selectedObject && (
                <div className="border-t border-gray-700 pt-4">
                    <h2 className="text-sm uppercase text-gray-400 mb-3 font-semibold">Properties</h2>
                    <div className="space-y-3 text-sm">
                        <div className="flex justify-between">
                            <span className="text-gray-400">Type</span>
                            <span className="capitalize">{selectedObject.type}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-400">ID</span>
                            <span className="font-mono text-xs">{selectedObject.id.slice(0, 8)}</span>
                        </div>

                        {/* Position display */}
                        <div>
                            <span className="text-gray-400 text-xs block mb-1">Position</span>
                            <div className="grid grid-cols-3 gap-1">
                                <div className="bg-gray-700/50 rounded px-2 py-1 text-center">
                                    <span className="text-gray-500 text-[10px] block">X</span>
                                    <span className="text-xs font-mono">{formatCoord(selectedObject.position?.[0])}</span>
                                </div>
                                <div className="bg-gray-700/50 rounded px-2 py-1 text-center">
                                    <span className="text-gray-500 text-[10px] block">Y</span>
                                    <span className="text-xs font-mono">{formatCoord(selectedObject.position?.[1])}</span>
                                </div>
                                <div className="bg-gray-700/50 rounded px-2 py-1 text-center">
                                    <span className="text-gray-500 text-[10px] block">Z</span>
                                    <span className="text-xs font-mono">{formatCoord(selectedObject.position?.[2])}</span>
                                </div>
                            </div>
                        </div>

                        {/* Size controls */}
                        {isEditMode && (
                            <div>
                                <span className="text-gray-400 text-xs block mb-1">Size</span>
                                {['W', 'H', 'D'].map((label, i) => (
                                    <div key={label} className="flex items-center justify-between mb-1">
                                        <span className="text-gray-500 text-xs w-4">{label}</span>
                                        <div className="flex items-center gap-1">
                                            <button
                                                onClick={() => {
                                                    const newSize = [...selectedObject.size];
                                                    newSize[i] = Math.max(0.5, newSize[i] - 0.5);
                                                    updateObject(selectedObject.id, { size: newSize });
                                                }}
                                                className="w-6 h-6 bg-gray-700 hover:bg-gray-600 rounded text-xs flex items-center justify-center transition"
                                            >−</button>
                                            <span className="text-xs font-mono w-8 text-center">{formatCoord(selectedObject.size?.[i])}</span>
                                            <button
                                                onClick={() => {
                                                    const newSize = [...selectedObject.size];
                                                    newSize[i] = newSize[i] + 0.5;
                                                    updateObject(selectedObject.id, { size: newSize });
                                                }}
                                                className="w-6 h-6 bg-gray-700 hover:bg-gray-600 rounded text-xs flex items-center justify-center transition"
                                            >+</button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        <button
                            onClick={() => removeObject(selectedObject.id)}
                            className="w-full mt-4 bg-red-500/80 hover:bg-red-500 text-white py-2 rounded transition"
                        >
                            Delete Object
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};
