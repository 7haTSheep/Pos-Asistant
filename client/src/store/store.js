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

    // Tool state
    activeTool: 'pointer',
    mode: 'view',
    selection: null,
    historyPast: [],
    historyFuture: [],

    // Zone state
    zones: [],
    zoneToolActive: false,
    zoneDrawing: null,

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
    }),

    /**
     * Serialize the current layout for storage
     * @returns {Object} Serialized layout data
     */
    serializeLayout: () => {
        const state = get();
        return {
            version: '1.0',
            objects: state.objects,
            zones: state.zones,
            settings: {
                gridSize: state.gridSize,
                snapToGrid: state.snapToGrid,
                viewMode: state.viewMode,
                floorDimensions: state.floorDimensions
            }
        };
    },

    /**
     * Load a layout from serialized data
     * @param {Object} layoutData - Serialized layout data
     */
    loadLayout: (layoutData) => {
        if (!layoutData) return;
        set({
            objects: layoutData.objects || [],
            selectedId: null,
            gridSize: layoutData.settings?.gridSize || 1,
            snapToGrid: layoutData.settings?.snapToGrid ?? true,
            viewMode: layoutData.settings?.viewMode || '2D',
            floorDimensions: layoutData.settings?.floorDimensions || { width: 50, depth: 50 },
            zones: layoutData.zones || [],
        });
    },

    /**
     * Set the active tool
     * @param {string} tool - Tool name ('pointer', 'pencil', 'eraser')
     */
    setActiveTool: (tool) => set({ activeTool: tool }),

    /**
     * Set the mode
     * @param {string} mode - Mode name ('view', 'edit')
     */
    setMode: (mode) => set({ mode }),

    /**
     * Set the selection
     * @param {Object|null} selection - Selection object
     */
    setSelection: (selection) => set({ selection }),

    /**
     * Undo the last action
     */
    undo: () => {
        const state = get();
        if (state.historyPast.length === 0) return;
        const previous = state.historyPast[state.historyPast.length - 1];
        const current = {
            objects: state.objects,
            selectedId: state.selectedId,
        };
        set({
            objects: previous.objects,
            selectedId: previous.selectedId,
            historyPast: state.historyPast.slice(0, -1),
            historyFuture: [current, ...state.historyFuture],
        });
    },

    /**
     * Redo the last undone action
     */
    redo: () => {
        const state = get();
        if (state.historyFuture.length === 0) return;
        const next = state.historyFuture[0];
        const current = {
            objects: state.objects,
            selectedId: state.selectedId,
        };
        set({
            objects: next.objects,
            selectedId: next.selectedId,
            historyPast: [...state.historyPast, current],
            historyFuture: state.historyFuture.slice(1),
        });
    },

    /**
     * Push current state to history (call before making changes)
     */
    pushHistory: () => {
        const state = get();
        const current = {
            objects: state.objects,
            selectedId: state.selectedId,
        };
        set({
            historyPast: [...state.historyPast, current],
            historyFuture: [],
        });
    },

    /**
     * Set zone tool active state
     * @param {boolean} active - Whether zone tool is active
     */
    setZoneToolActive: (active) => set({ zoneToolActive: active }),

    /**
     * Start drawing a zone
     * @param {Object} startPoint - Starting point {x, y, z}
     */
    startZoneDrawing: (startPoint) => set({ zoneDrawing: { start: startPoint, current: startPoint } }),

    /**
     * Update zone drawing current position
     * @param {Object} currentPoint - Current point {x, y, z}
     */
    updateZoneDrawing: (currentPoint) => {
        const state = get();
        if (!state.zoneDrawing) return;
        set({ zoneDrawing: { ...state.zoneDrawing, current: currentPoint } });
    },

    /**
     * Finish drawing a zone
     * @param {string} name - Zone name
     */
    finishZoneDrawing: (name = 'Zone') => {
        const state = get();
        if (!state.zoneDrawing) return;

        const start = state.zoneDrawing.start;
        const current = state.zoneDrawing.current;

        // Calculate bounds from drag rectangle
        const rowMin = Math.floor(Math.min(start.z, current.z));
        const rowMax = Math.floor(Math.max(start.z, current.z));
        const colMin = Math.floor(Math.min(start.x, current.x));
        const colMax = Math.floor(Math.max(start.x, current.x));

        const newZone = {
            id: `zone-${Date.now()}`,
            name: `${name} ${state.zones.length + 1}`,
            rowMin: Math.max(1, rowMin),
            rowMax: Math.max(1, rowMax),
            colMin: Math.max(1, colMin),
            colMax: Math.max(1, colMax),
            layerMin: 1,
            layerMax: 1,
        };

        set({
            zones: [...state.zones, newZone],
            zoneDrawing: null,
        });
    },

    /**
     * Cancel zone drawing
     */
    cancelZoneDrawing: () => set({ zoneDrawing: null }),

    /**
     * Remove a zone
     * @param {string} zoneId - Zone ID to remove
     */
    removeZone: (zoneId) => set((state) => ({
        zones: state.zones.filter(z => z.id !== zoneId),
    })),

    /**
     * Get zone by ID
     * @param {string} zoneId - Zone ID
     */
    getZone: (zoneId) => {
        const state = get();
        return state.zones.find(z => z.id === zoneId) || null;
    },

    /**
     * Load zones from layout data
     * @param {Array} zones - Zones array
     */
    loadZones: (zones) => set({ zones: zones || [] })
}));
