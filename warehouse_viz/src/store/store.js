import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';

export const useStore = create((set) => ({
    objects: [],
    items: [],
    zones: [],
    selection: null, // { type: 'object'|'item'|'zone', id: string }
    mode: 'view', // 'view', 'edit', 'zone_edit'

    // Actions
    addObject: (type, position) => set((state) => ({
        objects: [...state.objects, {
            id: uuidv4(),
            type,
            position, // [x, y, z]
            rotation: [0, 0, 0],
            size: type === 'shelf' ? [3, 4, 1.5] : type === 'fridge' ? [2, 3, 1.5] : [2, 2, 1.5], // Default sizes
            zoneId: null,
            grid: { rows: 4, cols: 3, depth: 2 } // Default grid
        }]
    })),

    updateObject: (id, updates) => set((state) => ({
        objects: state.objects.map(obj => obj.id === id ? { ...obj, ...updates } : obj)
    })),

    removeObject: (id) => set((state) => ({
        objects: state.objects.filter(obj => obj.id !== id),
        // Cleanup items in that object
        items: state.items.filter(item => item.objectId !== id)
    })),

    addItem: (objectId, gridPos, meta) => set((state) => ({
        items: [...state.items, {
            id: uuidv4(),
            objectId,
            gridPos, // { row, col, layer }
            ...meta // name, sku, quantity, etc.
        }]
    })),

    removeItem: (id) => set((state) => ({
        items: state.items.filter(item => item.id !== id)
    })),

    setSelection: (sel) => set({ selection: sel }),
    setMode: (mode) => set({ mode }),
}));
