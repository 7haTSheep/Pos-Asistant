import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';
import { getObjectType } from '../utils/objectTypes';

/**
 * Floor Plan Designer Store
 *
 * Complete state management for warehouse floor planning with:
 * - Objects (furniture, equipment)
 * - Walls (structural elements)
 * - Fixtures (mounted items)
 * - Zones (inventory areas)
 * - Floors (multiple floor plans)
 * - History (undo/redo)
 */
export const useStore = create((set, get) => ({
    // ========== Core State ==========
    objects: [],
    walls: [],
    fixtures: [],
    zones: [],
    floors: [{
        id: 'default-floor',
        name: 'Default Floor',
        dimensions: { width: 50, depth: 50 },
        floorGrid: { cellSize: 1, visible: true },
    }],
    activeFloorId: 'default-floor',
    
    // Selection & Interaction
    selection: null,
    mode: 'edit', // 'edit' | 'view'
    activeTool: 'pointer', // 'pointer' | 'pencil' | 'eraser'
    
    // Placement State
    placementItem: null,
    fixturePreview: null,
    
    // History (undo/redo)
    historyPast: [],
    historyFuture: [],
    isInteracting: false,
    
    // Settings
    gridSize: 1,
    snapToGrid: true,
    floorDimensions: { width: 50, depth: 50 },

    // ========== History Management ==========
    
    beginInteraction: () => {
        const state = get();
        const snapshot = {
            objects: [...state.objects],
            walls: [...state.walls],
            fixtures: [...state.fixtures],
            zones: [...state.zones],
        };
        set({
            historyPast: [...state.historyPast, snapshot],
            historyFuture: [],
            isInteracting: true,
        });
    },
    
    endInteraction: () => {
        const state = get();
        if (!state.isInteracting) return;
        
        const snapshot = {
            objects: [...state.objects],
            walls: [...state.walls],
            fixtures: [...state.fixtures],
            zones: [...state.zones],
        };
        
        set((prevState) => ({
            historyPast: [...prevState.historyPast, snapshot],
            historyFuture: [],
            isInteracting: false,
        }));
    },
    
    undo: () => {
        const state = get();
        if (state.historyPast.length === 0) return;
        
        const previous = state.historyPast[state.historyPast.length - 1];
        const current = {
            objects: [...state.objects],
            walls: [...state.walls],
            fixtures: [...state.fixtures],
            zones: [...state.zones],
        };
        
        set({
            objects: previous.objects,
            walls: previous.walls,
            fixtures: previous.fixtures,
            zones: previous.zones,
            historyPast: state.historyPast.slice(0, -1),
            historyFuture: [current, ...state.historyFuture],
        });
    },
    
    redo: () => {
        const state = get();
        if (state.historyFuture.length === 0) return;
        
        const next = state.historyFuture[0];
        const current = {
            objects: [...state.objects],
            walls: [...state.walls],
            fixtures: [...state.fixtures],
            zones: [...state.zones],
        };
        
        set({
            objects: next.objects,
            walls: next.walls,
            fixtures: next.fixtures,
            zones: next.zones,
            historyPast: [...state.historyPast, current],
            historyFuture: state.historyFuture.slice(1),
        });
    },

    // ========== Object Management ==========

    /**
     * Add a new object to the scene
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
            size: objectType.defaultDimensions,
            floorId: get().activeFloorId,
        };

        set((state) => ({
            objects: [...state.objects, newObject],
            selection: { type: 'object', id: newObject.id },
        }));
    },

    /**
     * Update an existing object
     */
    updateObject: (id, updates, options = {}) => {
        const skipHistory = options?.skipHistory;
        
        set((state) => ({
            objects: state.objects.map(obj =>
                obj.id === id ? { ...obj, ...updates } : obj
            ),
        }));
        
        if (!skipHistory && !get().isInteracting) {
            get().endInteraction();
        }
    },

    /**
     * Remove an object
     */
    removeObject: (id) => set((state) => ({
        objects: state.objects.filter(obj => obj.id !== id),
        selection: state.selection?.id === id ? null : state.selection,
    })),

    // ========== Wall Management ==========

    addWall: (start, end, options = {}) => {
        const newWall = {
            id: uuidv4(),
            start,
            end,
            thickness: options.thickness || 0.35,
            height: options.height || 1,
            floorId: get().activeFloorId,
        };

        set((state) => ({
            walls: [...state.walls, newWall],
            selection: { type: 'wall', id: newWall.id },
        }));
    },

    updateWall: (id, updates, options = {}) => {
        const skipHistory = options?.skipHistory;
        
        set((state) => ({
            walls: state.walls.map(wall =>
                wall.id === id ? { ...wall, ...updates } : wall
            ),
        }));
        
        if (!skipHistory && !get().isInteracting) {
            get().endInteraction();
        }
    },

    removeWall: (id) => set((state) => ({
        walls: state.walls.filter(wall => wall.id !== id),
        selection: state.selection?.id === id ? null : state.selection,
    })),

    // ========== Fixture Management ==========

    addFixture: (fixtureData) => {
        const newFixture = {
            id: uuidv4(),
            floorId: get().activeFloorId,
            ...fixtureData,
        };

        set((state) => ({
            fixtures: [...state.fixtures, newFixture],
            selection: { type: 'fixture', id: newFixture.id },
        }));
    },

    removeFixture: (id) => set((state) => ({
        fixtures: state.fixtures.filter(fixture => fixture.id !== id),
        selection: state.selection?.id === id ? null : state.selection,
    })),

    // ========== Zone Management ==========

    addZone: (zoneData) => {
        const newZone = {
            id: uuidv4(),
            floorId: get().activeFloorId,
            ...zoneData,
        };

        set((state) => ({
            zones: [...state.zones, newZone],
            selection: { type: 'zone', id: newZone.id },
        }));
    },

    updateZone: (id, updates) => set((state) => ({
        zones: state.zones.map(zone =>
            zone.id === id ? { ...zone, ...updates } : zone
        ),
    })),

    removeZone: (id) => set((state) => ({
        zones: state.zones.filter(zone => zone.id !== id),
        selection: state.selection?.id === id ? null : state.selection,
    })),

    // ========== Floor Management ==========

    addFloor: (floorData) => {
        const newFloor = {
            id: uuidv4(),
            name: floorData.name || 'New Floor',
            dimensions: floorData.dimensions || { width: 50, depth: 50 },
            floorGrid: floorData.floorGrid || { cellSize: 1 },
            ...floorData,
        };

        set((state) => {
            const floors = [...state.floors, newFloor];
            return {
                floors,
                activeFloorId: newFloor.id,
            };
        });
        
        return newFloor.id;
    },

    setActiveFloor: (floorId) => set({ activeFloorId: floorId }),

    updateFloor: (id, updates) => set((state) => ({
        floors: state.floors.map(floor =>
            floor.id === id ? { ...floor, ...updates } : floor
        ),
    })),

    removeFloor: (id) => set((state) => {
        const floors = state.floors.filter(floor => floor.id !== id);
        return {
            floors,
            activeFloorId: state.activeFloorId === id ? (floors[0]?.id || null) : state.activeFloorId,
        };
    }),

    // ========== Selection & Mode ==========

    setSelection: (selection) => set({ selection }),

    setMode: (mode) => set({ mode }),

    setActiveTool: (tool) => set({ activeTool: tool }),

    setPlacementItem: (item) => set({ placementItem: item }),

    setFixturePreview: (preview) => set({ fixturePreview: preview }),

    // ========== Settings ==========

    setViewMode: (mode) => set({ viewMode: mode }),

    setGridSize: (size) => set({ gridSize: size }),

    setSnapToGrid: (enabled) => set({ snapToGrid: enabled }),

    setFloorDimensions: (dimensions) => set({ floorDimensions: dimensions }),

    // ========== Layout Serialization ==========

    serializeLayout: () => {
        const state = get();
        return {
            version: '2.0',
            floors: state.floors,
            activeFloorId: state.activeFloorId,
            objects: state.objects,
            walls: state.walls,
            fixtures: state.fixtures,
            zones: state.zones,
            settings: {
                gridSize: state.gridSize,
                snapToGrid: state.snapToGrid,
                mode: state.mode,
            },
        };
    },

    loadLayout: (layoutData) => {
        set({
            floors: layoutData.floors || [],
            activeFloorId: layoutData.activeFloorId || null,
            objects: layoutData.objects || [],
            walls: layoutData.walls || [],
            fixtures: layoutData.fixtures || [],
            zones: layoutData.zones || [],
            selection: null,
            placementItem: null,
            fixturePreview: null,
            historyPast: [],
            historyFuture: [],
            isInteracting: false,
            gridSize: layoutData.settings?.gridSize || 1,
            snapToGrid: layoutData.settings?.snapToGrid ?? true,
            mode: layoutData.settings?.mode || 'edit',
        });
    },

    // ========== Legacy Compatibility ==========

    getSceneData: () => {
        const state = get();
        return {
            version: '1.0',
            objects: state.objects,
            settings: {
                gridSize: state.gridSize,
                snapToGrid: state.snapToGrid,
                viewMode: state.viewMode || '2D',
                floorDimensions: state.floorDimensions
            }
        };
    },

    loadScene: (sceneData) => set({
        objects: sceneData.objects || [],
        walls: [],
        fixtures: [],
        zones: [],
        selection: null,
        gridSize: sceneData.settings?.gridSize || 1,
        snapToGrid: sceneData.settings?.snapToGrid ?? true,
        viewMode: sceneData.settings?.viewMode || '2D',
        floorDimensions: sceneData.settings?.floorDimensions || { width: 50, depth: 50 },
        historyPast: [],
        historyFuture: [],
        isInteracting: false,
    }),

    clearScene: () => set({
        objects: [],
        walls: [],
        fixtures: [],
        zones: [],
        selection: null,
        placementItem: null,
        fixturePreview: null,
    }),
}));
