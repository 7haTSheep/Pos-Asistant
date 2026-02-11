import React from 'react';
import { useStore } from '../../store/store';
import { Box, Snowflake, Archive } from 'lucide-react';

export const Sidebar = () => {
    const addObject = useStore((state) => state.addObject);
    const selection = useStore((state) => state.selection);
    const objects = useStore((state) => state.objects);
    const removeObject = useStore((state) => state.removeObject);

    const selectedObject = selection?.type === 'object'
        ? objects.find(o => o.id === selection.id)
        : null;

    return (
        <div className="absolute top-0 left-0 h-full w-64 bg-gray-800 text-white p-4 overflow-y-auto z-10 shadow-lg">
            <h1 className="text-xl font-bold mb-6">Warehouse Viz</h1>

            <div className="mb-8">
                <h2 className="text-sm uppercase text-gray-400 mb-3 font-semibold">Add Object</h2>
                <div className="grid grid-cols-2 gap-2">
                    <button
                        draggable
                        onDragStart={(e) => e.dataTransfer.setData('type', 'shelf')}
                        onClick={() => addObject('shelf', [0, 1.5, 0])}
                        className="flex flex-col items-center justify-center p-3 bg-gray-700 hover:bg-gray-600 rounded transition cursor-grab active:cursor-grabbing"
                    >
                        <Archive size={24} className="mb-2 text-orange-400" />
                        <span className="text-xs">Shelf</span>
                    </button>

                    <button
                        draggable
                        onDragStart={(e) => e.dataTransfer.setData('type', 'fridge')}
                        onClick={() => addObject('fridge', [0, 1, 0])}
                        className="flex flex-col items-center justify-center p-3 bg-gray-700 hover:bg-gray-600 rounded transition cursor-grab active:cursor-grabbing"
                    >
                        <Snowflake size={24} className="mb-2 text-blue-300" />
                        <span className="text-xs">Fridge</span>
                    </button>

                    <button
                        draggable
                        onDragStart={(e) => e.dataTransfer.setData('type', 'freezer')}
                        onClick={() => addObject('freezer', [0, 0.5, 0])}
                        className="flex flex-col items-center justify-center p-3 bg-gray-700 hover:bg-gray-600 rounded transition cursor-grab active:cursor-grabbing"
                    >
                        <Box size={24} className="mb-2 text-cyan-200" />
                        <span className="text-xs">Freezer</span>
                    </button>
                </div>
            </div>

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

                        <button
                            onClick={() => removeObject(selectedObject.id)}
                            className="w-full mt-4 bg-red-500 hover:bg-red-600 text-white py-2 rounded transition"
                        >
                            Delete Object
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};
