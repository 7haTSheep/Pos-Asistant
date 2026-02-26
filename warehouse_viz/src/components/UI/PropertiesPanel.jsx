import React from 'react';
import { useStore } from '../../store/store';
import { Trash2, Move, RotateCcw, Maximize } from 'lucide-react';

export const PropertiesPanel = () => {
    const selection = useStore((state) => state.selection);
    const objects = useStore((state) => state.objects);
    const updateObject = useStore((state) => state.updateObject);
    const removeObject = useStore((state) => state.removeObject);

    const selectedObject = selection?.type === 'object'
        ? objects.find(o => o.id === selection.id)
        : null;

    const formatCoord = (val) => typeof val === 'number' ? val.toFixed(2) : '0.00';

    if (!selectedObject) {
        return (
            <div className="w-64 bg-gray-800 border-l border-gray-700 p-4 text-gray-400 text-sm">
                <p className="text-center mt-10">Select an object to view properties.</p>
                <div className="mt-8 border-t border-gray-700 pt-4">
                    <h3 className="font-semibold text-gray-300 mb-2">Scene Settings</h3>
                    <div className="space-y-2">
                        <label className="flex items-center justify-between text-xs">
                            <span>Grid Size</span>
                            <input type="number" defaultValue={50} className="w-16 bg-gray-900 border border-gray-700 rounded px-2 py-1 text-right" disabled />
                        </label>
                        <label className="flex items-center justify-between text-xs">
                            <span>Snap</span>
                            <input type="checkbox" defaultChecked className="form-checkbox bg-gray-900 border-gray-700 rounded text-blue-500" />
                        </label>
                    </div>
                </div>
            </div>
        );
    }

    const handleChange = (prop, axis, value) => {
        const newProps = [...selectedObject[prop]];
        newProps[axis] = parseFloat(value) || 0;
        updateObject(selectedObject.id, { [prop]: newProps });
    };

    return (
        <div className="w-72 bg-gray-800 border-l border-gray-700 flex flex-col h-full overflow-y-auto">
            <div className="p-4 border-b border-gray-700">
                <h2 className="font-bold text-white text-lg capitalize">{selectedObject.type}</h2>
                <div className="text-xs text-gray-500 font-mono mt-1">ID: {selectedObject.id.slice(0, 8)}</div>
            </div>

            <div className="p-4 space-y-6">
                {/* Transform: Position */}
                <div>
                    <div className="flex items-center gap-2 mb-2 text-gray-300 text-sm font-medium">
                        <Move size={14} /> <span>Position</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                        {['X', 'Y', 'Z'].map((label, i) => (
                            <div key={label} className="relative">
                                <label className="absolute left-2 top-1.5 text-[10px] text-gray-500 font-bold">{label}</label>
                                <input
                                    type="number"
                                    step="0.1"
                                    value={formatCoord(selectedObject.position[i])}
                                    onChange={(e) => handleChange('position', i, e.target.value)}
                                    className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1 pl-6 text-sm text-white focus:border-blue-500 focus:outline-none"
                                />
                            </div>
                        ))}
                    </div>
                </div>

                {/* Transform: Rotation */}
                <div>
                    <div className="flex items-center gap-2 mb-2 text-gray-300 text-sm font-medium">
                        <RotateCcw size={14} /> <span>Rotation (Rad)</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                        {['X', 'Y', 'Z'].map((label, i) => (
                            <div key={label} className="relative">
                                <label className="absolute left-2 top-1.5 text-[10px] text-gray-500 font-bold">{label}</label>
                                <input
                                    type="number"
                                    step="0.1"
                                    value={formatCoord(selectedObject.rotation[i])}
                                    onChange={(e) => handleChange('rotation', i, e.target.value)}
                                    className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1 pl-6 text-sm text-white focus:border-blue-500 focus:outline-none"
                                />
                            </div>
                        ))}
                    </div>
                </div>

                {/* Transform: Size */}
                <div>
                    <div className="flex items-center gap-2 mb-2 text-gray-300 text-sm font-medium">
                        <Maximize size={14} /> <span>Dimensions</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                        {['W', 'H', 'D'].map((label, i) => (
                            <div key={label} className="relative">
                                <label className="absolute left-2 top-1.5 text-[10px] text-gray-500 font-bold">{label}</label>
                                <input
                                    type="number"
                                    step="0.1"
                                    min="0.1"
                                    value={formatCoord(selectedObject.size[i])}
                                    onChange={(e) => handleChange('size', i, e.target.value)}
                                    className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1 pl-6 text-sm text-white focus:border-blue-500 focus:outline-none"
                                />
                            </div>
                        ))}
                    </div>
                </div>

                {/* Actions */}
                <div className="pt-4 border-t border-gray-700">
                    <button
                        onClick={() => removeObject(selectedObject.id)}
                        className="w-full flex items-center justify-center gap-2 bg-red-900/30 hover:bg-red-900/50 text-red-400 border border-red-900/50 py-2 rounded-lg transition"
                    >
                        <Trash2 size={16} />
                        <span>Delete Object</span>
                    </button>
                </div>
            </div>
        </div>
    );
};
