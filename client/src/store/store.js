import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';
import { getObjectType } from '../utils/objectTypes';

/**
 * Floor Plan Designer Store
 * 
 * State Interface:
 * - objects: Array of Object3DData (id, type, position, rotation, dimensions)
 * - selectedId: string | null (currently selected object ID)
 * - viewMode: '2D' | '3D' (current view mode)
 * - gridSize: number (grid cell size in meters)
 * - snapToGrid: boolean (whether to snap objects to grid)
 * - floorDimensions: { width: number, depth: number } (floor size in meters)
 */
export const useStore = create((set, get) => ({
    // State
    objects: [],
    selectedId: null,
    viewMode: '2D',
    gridSize: 1,
    snapToGrid: true,
    floorDimensions: { width: 50, depth: 50 },

    // Actions

    /**
     * Add a new object to the scene
     * @param {string} type - Object type ID (e.g., 'wall', 'desk')
     * @param {[number, number, number]} position - Optional position [x, y, z], defaults to [0, 0, 0]
     */
    addObject: (type, position = [0, 0, 0]) => {
        const objectType = getObjectType(type);
        if (!objectType) {
            console.error(`Unknown object type: ${type}`);
            return;
        }

        const newObject = {
            id: uuidv4(),
            type,
            position,
            rotation: [0, 0, 0],
            dimensions: [...objectType.defaultDimensions]
        };

        set((state) => ({
            objects: [...state.objects, newObject],
            selectedId: newObject.id // Auto-select newly added object
        }));
    },

    /**
     * Update an existing object with partial updates
     * @param {string} id - Object ID
     * @param {Partial<Object3DData>} updates - Fields to update
     */
    updateObject: (id, updates) => set((state) => ({
        objects: state.objects.map(obj =>
            obj.id === id ? { ...obj, ...updates } : obj
        )
    })),

    /**
     * Remove an object from the scene
     * @param {string} id - Object ID to remove
     */
    removeObject: (id) => set((state) => ({
        objects: state.objects.filter(obj => obj.id !== id),
        // Clear selection if the removed object was selected
        selectedId: state.selectedId === id ? null : state.selectedId
    })),

    /**
     * Set the currently selected object
     * @param {string | null} id - Object ID to select, or null to deselect
     */
    setSelection: (id) => set({ selectedId: id }),

    /**
     * Set the view mode
     * @param {'2D' | '3D'} mode - View mode
     */
    setViewMode: (mode) => set({ viewMode: mode }),

    /**
     * Set the grid size
     * @param {number} size - Grid cell size in meters
     */
    setGridSize: (size) => set({ gridSize: size }),

    /**
     * Set whether to snap objects to grid
     * @param {boolean} enabled - Whether snap to grid is enabled
     */
    setSnapToGrid: (enabled) => set({ snapToGrid: enabled }),

    /**
     * Set floor dimensions
     * @param {{ width: number, depth: number }} dimensions - Floor dimensions in meters
     */
    setFloorDimensions: (dimensions) => set({ floorDimensions: dimensions }),

    /**
     * Get complete scene data for serialization
     * @returns {SceneData} Complete scene data
     */
    getSceneData: () => {
        const state = get();
        return {
            version: '1.0',
            objects: state.objects,
            settings: {
                gridSize: state.gridSize,
                snapToGrid: state.snapToGrid,
                viewMode: state.viewMode,
                floorDimensions: state.floorDimensions
            }
        };
    },

    /**
     * Load scene data from serialized format
     * @param {SceneData} sceneData - Scene data to load
     */
    loadScene: (sceneData) => set({
        objects: sceneData.objects || [],
        selectedId: null,
        gridSize: sceneData.settings?.gridSize || 1,
        snapToGrid: sceneData.settings?.snapToGrid ?? true,
        viewMode: sceneData.settings?.viewMode || '2D',
        floorDimensions: sceneData.settings?.floorDimensions || { width: 50, depth: 50 }
    }),

    /**
     * Clear all objects from the scene
     */
    clearScene: () => set({
        objects: [],
        selectedId: null
    })
}));
