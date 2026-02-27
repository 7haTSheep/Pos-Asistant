import React, { useState, useMemo } from 'react';
import { useStore } from '../../store/store';
import { OBJECT_TYPES } from '../../utils/objectTypes';
import {
    Search,
    Square,
    DoorOpen,
    Box,
    Grid3x3,
    Package,
    Refrigerator,
    Snowflake,
    RectangleHorizontal,
    Armchair,
    Table,
    Archive
} from 'lucide-react';

// Map icon names to Lucide components
const ICON_MAP = {
    Square,
    DoorOpen,
    Box,
    Grid3x3,
    Package,
    Refrigerator,
    Snowflake,
    RectangleHorizontal,
    Armchair,
    Table,
    Archive
};

export const LibraryPanel = () => {
    const addObject = useStore((state) => state.addObject);
    const setPlacementItem = useStore((state) => state.setPlacementItem);
    const [activeCategory, setActiveCategory] = useState('All');
    const [searchQuery, setSearchQuery] = useState('');

    // Filter objects based on search query and active category
    const filteredObjects = useMemo(() => {
        return OBJECT_TYPES.filter(obj => {
            const matchesSearch = obj.name.toLowerCase().includes(searchQuery.toLowerCase());
            const matchesCategory = activeCategory === 'All' || obj.category === activeCategory;
            return matchesSearch && matchesCategory;
        });
    }, [searchQuery, activeCategory]);

    // Handle drag start for drag-and-drop
    const handleDragStart = (e, objectType) => {
        const item = {
            kind: 'object',
            type: objectType.id,
            name: objectType.name,
            defaultDimensions: objectType.defaultDimensions,
        };
        e.dataTransfer.setData('application/x-warehouse-catalog-item', JSON.stringify(item));
        e.dataTransfer.effectAllowed = 'copy';
    };

    // Handle click to add object at default position
    const handleClick = (objectType) => {
        addObject(objectType.id);
    };

    return (
        <div className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col h-full z-10">
            {/* Search Input */}
            <div className="p-4 border-b border-gray-700">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" size={14} />
                    <input
                        type="text"
                        placeholder="Search objects..."
                        className="w-full bg-gray-900 text-sm text-gray-300 rounded-lg pl-9 pr-3 py-2 border border-gray-700 focus:border-blue-500 focus:outline-none placeholder-gray-600"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
            </div>

            {/* Category Tabs */}
            <div className="flex border-b border-gray-700">
                {['All', 'Structure', 'Warehouse', 'Office'].map((category) => (
                    <button
                        key={category}
                        onClick={() => setActiveCategory(category)}
                        className={`flex-1 py-3 text-xs font-medium text-center transition-colors ${
                            activeCategory === category
                                ? 'text-blue-400 border-b-2 border-blue-400'
                                : 'text-gray-400 hover:text-gray-300'
                        }`}
                    >
                        {category}
                    </button>
                ))}
            </div>

            {/* Object List */}
            <div className="p-4 overflow-y-auto flex-1 custom-scrollbar">
                <div className="grid grid-cols-2 gap-3">
                    {filteredObjects.map((item) => {
                        const IconComponent = ICON_MAP[item.icon] || Box;
                        return (
                            <button
                                key={item.id}
                                draggable
                                onDragStart={(e) => handleDragStart(e, item)}
                                onClick={() => handleClick(item)}
                                className="group flex flex-col items-center p-3 bg-gray-750 border border-gray-700 rounded-xl hover:bg-gray-700 hover:border-gray-600 transition-all cursor-grab active:cursor-grabbing text-center"
                            >
                                <div className="p-3 rounded-lg bg-gray-800 group-hover:bg-gray-600 transition-colors mb-2 text-gray-400">
                                    <IconComponent size={24} strokeWidth={1.5} />
                                </div>
                                <span className="text-xs text-gray-300 font-medium group-hover:text-white">
                                    {item.name}
                                </span>
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Footer Hint */}
            <div className="p-4 border-t border-gray-700 text-center">
                <p className="text-[10px] text-gray-500">Drag items to the canvas</p>
            </div>
        </div>
    );
};
