import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';

const DEFAULT_OBJECT_SIZE = {
    storage_shelf: [20, 4, 10],
    pallet_rack: [20, 4.5, 10],
    bin_rack: [20, 3.2, 10],
    cantilever_rack: [20, 4, 10],
    pallet_stack: [20, 2.2, 10],
    walk_in_refrigerator: [20, 3.2, 10],
    walk_in_freezer: [20, 3.4, 10],
    cold_room: [20, 3.6, 10],
    chiller_unit: [20, 2.4, 10],
    forklift_bay: [20, 2.2, 10],
    loading_dock: [20, 1.8, 10],
    conveyor: [20, 1.6, 10],
    packing_table: [20, 1.8, 10],
    sort_station: [20, 1.8, 10],
    fire_extinguisher: [20, 1.2, 10],
    first_aid_station: [20, 1.4, 10],
    electrical_panel: [20, 2.2, 10],
    charging_station: [20, 1.8, 10],

    shelf: [3, 4, 1.5],
    fridge: [2, 3, 1.5],
    freezer: [2, 2, 1.5],
    door: [1.2, 2.2, 0.3],
    window: [1.8, 1.2, 0.25],
    opening: [1.5, 2, 0.25],
    pallet: [1.4, 0.6, 1],
    bin: [1, 0.8, 1],
    desk: [2.4, 1.2, 1.2],
    desk_lamp: [0.5, 0.6, 0.5],
    under_desk_cabinet: [1.1, 1.1, 0.8],
    chair: [0.9, 1, 0.9],
    monitor: [0.9, 0.5, 0.25],
    laptop: [0.9, 0.15, 0.6],
    computer: [0.25, 0.9, 0.9],
    keyboard: [0.6, 0.08, 0.25],
    printer: [0.9, 0.5, 0.7],
    cabinet: [1.1, 1.2, 0.65],
    lower_cabinet: [1.1, 0.9, 0.65],
    corner_table: [1.4, 0.9, 1.4],
    stove: [1, 0.9, 0.7],
    oven: [1, 0.9, 0.7],
    dishwasher: [0.9, 0.9, 0.7],
    microwave: [0.9, 0.5, 0.6],
    sofa: [2.2, 1.1, 0.95],
    armchair: [1.2, 1.1, 1],
    table: [1.4, 0.9, 1.1],
    table_round: [1.2, 0.9, 1.2],
    tv: [1.4, 0.7, 0.25],
    plant: [0.6, 0.9, 0.6],
};

const createFloor = (name) => ({
    id: uuidv4(),
    name,
    dimensions: { width: 50, depth: 50 },
    floorGrid: { visible: true, cellSize: 1 },
});

const clampInt = (value, min = 1) => Math.max(min, Number.parseInt(value, 10) || min);

const normalizeSlot = (slot) => ({
    row: clampInt(slot?.row),
    col: clampInt(slot?.col),
    layer: clampInt(slot?.layer),
});

const slotKey = (slot) => `${slot.row}:${slot.col}:${slot.layer}`;

const floorCode = (name) =>
    (name || 'FLOOR')
        .toUpperCase()
        .replace(/[^A-Z0-9]/g, '')
        .slice(0, 6) || 'FLOOR';

const buildLocationCode = (floorName, objectId, slot) =>
    `${floorCode(floorName)}-O${objectId.slice(0, 6).toUpperCase()}-R${slot.row}C${slot.col}L${slot.layer}`;

const ZONE_COLORS = ['#fb7185', '#f97316', '#fbbf24', '#34d399', '#60a5fa'];

const normalizeRange = (a, b) => {
    const left = Math.max(1, Number.isFinite(Number(a)) ? Number(a) : 1);
    const right = Math.max(1, Number.isFinite(Number(b)) ? Number(b) : 1);
    const low = Math.min(left, right);
    const high = Math.max(left, right);
    return [low, high];
};

const createZoneEntry = (input, floorId, nextIndex) => {
    const [rowMin, rowMax] = normalizeRange(input.rowMin, input.rowMax);
    const [colMin, colMax] = normalizeRange(input.colMin, input.colMax);
    const [layerMin, layerMax] = normalizeRange(input.layerMin, input.layerMax);
    return {
        id: uuidv4(),
        name: input.name?.trim() || `Zone ${nextIndex}`,
        rowMin,
        rowMax,
        colMin,
        colMax,
        layerMin,
        layerMax,
        floorId,
        color: input.color || ZONE_COLORS[nextIndex % ZONE_COLORS.length],
    };
};
const initialFloor = createFloor('Ground Floor');
const HISTORY_LIMIT = 60;

const snapshotState = (state) => ({
    floors: state.floors,
    activeFloorId: state.activeFloorId,
    objects: state.objects,
    items: state.items,
    walls: state.walls,
    fixtures: state.fixtures,
    zones: state.zones,
    selection: state.selection,
    mode: state.mode,
    activeTool: state.activeTool,
    placementItem: state.placementItem,
});

const withHistory = (state, partial) => ({
    ...partial,
    historyPast: [...state.historyPast, snapshotState(state)].slice(-HISTORY_LIMIT),
    historyFuture: [],
});

const withOptionalHistory = (state, partial, options = {}) =>
    options?.skipHistory ? partial : withHistory(state, partial);

export const useStore = create((set, get) => ({
    floors: [initialFloor],
    activeFloorId: initialFloor.id,
    objects: [],
    items: [],
    walls: [],
    fixtures: [], // doors/windows/openings attached to walls
    zones: [],
    selection: null, // { type: 'object'|'wall'|'item'|'zone', id: string }
    mode: 'view', // 'view', 'edit'
    activeTool: 'pointer', // 'pointer' | 'pencil' | 'eraser'
    placementItem: null, // catalog item staged for placement
    historyPast: [],
    historyFuture: [],
    interactionActive: false,

    addFloor: (name) =>
        set((state) => {
            const newFloor = createFloor(name?.trim() || `Floor ${state.floors.length + 1}`);
            return withHistory(state, {
                floors: [...state.floors, newFloor],
                activeFloorId: newFloor.id,
                selection: null,
            });
        }),

    updateFloor: (id, updates) =>
        set((state) => withHistory(state, {
            floors: state.floors.map((floor) => {
                if (floor.id !== id) return floor;
                return {
                    ...floor,
                    ...updates,
                    dimensions: {
                        ...floor.dimensions,
                        ...(updates.dimensions || {}),
                    },
                    floorGrid: {
                        ...floor.floorGrid,
                        ...(updates.floorGrid || {}),
                    },
                };
            }),
        })),

    removeFloor: (id) =>
        set((state) => {
            if (state.floors.length === 1) return state;

            const remainingFloors = state.floors.filter((floor) => floor.id !== id);
            const newActiveFloorId =
                state.activeFloorId === id ? remainingFloors[0].id : state.activeFloorId;
            const remainingObjectIds = new Set(
                state.objects.filter((obj) => obj.floorId !== id).map((obj) => obj.id),
            );

        return withHistory(state, {
            floors: remainingFloors,
            activeFloorId: newActiveFloorId,
            objects: state.objects.filter((obj) => obj.floorId !== id),
            items: state.items.filter((item) => remainingObjectIds.has(item.objectId)),
            walls: state.walls.filter((wall) => wall.floorId !== id),
            fixtures: state.fixtures.filter((fixture) => fixture.floorId !== id),
            zones: state.zones.filter((zone) => zone.floorId !== id),
            selection: null,
        });
        }),

    setActiveFloor: (id) =>
        set((state) => {
            if (!state.floors.some((floor) => floor.id === id)) return state;
            return { activeFloorId: id, selection: null };
        }),

    addObject: (type, position) =>
        set((state) => withHistory(state, {
            objects: [
                ...state.objects,
                {
                    id: uuidv4(),
                    floorId: state.activeFloorId,
                    type,
                    position,
                    rotation: [0, 0, 0],
                    size: DEFAULT_OBJECT_SIZE[type] || [20, 2, 10],
                    zoneId: null,
                    grid: { rows: 4, cols: 3, layers: 2 },
                },
            ],
        })),

    updateObject: (id, updates, options = {}) =>
        set((state) => withOptionalHistory(state, {
            objects: state.objects.map((obj) => {
                if (obj.id !== id) return obj;
                return {
                    ...obj,
                    ...updates,
                    grid: updates.grid ? { ...obj.grid, ...updates.grid } : obj.grid,
                };
            }),
        }, options)),

    removeObject: (id) =>
        set((state) => withHistory(state, {
            objects: state.objects.filter((obj) => obj.id !== id),
            items: state.items.filter((item) => item.objectId !== id),
            selection: state.selection?.type === 'object' && state.selection.id === id ? null : state.selection,
        })),

    scanItemToSlot: (objectId, rawSlot, barcode, quantity = 1, meta = {}) =>
        set((state) => {
            const trimmedBarcode = (barcode || '').trim();
            if (!trimmedBarcode) return state;

            const object = state.objects.find((obj) => obj.id === objectId);
            if (!object) return state;

            const slot = normalizeSlot(rawSlot);
            const key = slotKey(slot);
            const floor = state.floors.find((item) => item.id === object.floorId);
            const locationCode = buildLocationCode(floor?.name, object.id, slot);
            const qty = Math.max(1, Number.parseInt(quantity, 10) || 1);

            const existing = state.items.find(
                (item) =>
                    item.objectId === objectId &&
                    item.barcode === trimmedBarcode &&
                    slotKey(item.slot) === key,
            );

            if (existing) {
                return {
                    items: state.items.map((item) =>
                        item.id === existing.id
                            ? { ...item, quantity: (item.quantity || 0) + qty, updatedAt: Date.now() }
                            : item,
                    ),
                };
            }

            return {
                items: [
                    ...state.items,
                    {
                        id: uuidv4(),
                        floorId: object.floorId,
                        objectId,
                        slot,
                        locationCode,
                        barcode: trimmedBarcode,
                        quantity: qty,
                        ...meta,
                        createdAt: Date.now(),
                        updatedAt: Date.now(),
                    },
                ],
            };
        }),

    removeItem: (id) =>
        set((state) => withHistory(state, {
            items: state.items.filter((item) => item.id !== id),
        })),

    addWall: (start, end, options = {}) =>
        set((state) => withHistory(state, {
            walls: [
                ...state.walls,
                {
                    id: uuidv4(),
                    floorId: state.activeFloorId,
                    start,
                    end,
                    thickness: options.thickness || 0.35,
                    height: options.height || 1,
                },
            ],
        })),

    removeWall: (id) =>
        set((state) => withHistory(state, {
            walls: state.walls.filter((wall) => wall.id !== id),
            fixtures: state.fixtures.filter((fixture) => fixture.wallId !== id),
            selection: state.selection?.type === 'wall' && state.selection.id === id ? null : state.selection,
        })),

    updateWall: (id, updates, options = {}) =>
        set((state) => withOptionalHistory(state, {
            walls: state.walls.map((wall) => {
                if (wall.id !== id) return wall;
                return {
                    ...wall,
                    ...updates,
                };
            }),
        }, options)),

    clearFloorWalls: (floorId) =>
        set((state) => withHistory(state, {
            walls: state.walls.filter((wall) => wall.floorId !== floorId),
            fixtures: state.fixtures.filter((fixture) => fixture.floorId !== floorId),
            zones: state.zones.filter((zone) => zone.floorId !== floorId),
        })),

    addFixture: (fixture) =>
        set((state) => withHistory(state, {
            fixtures: [
                ...state.fixtures,
                {
                    id: uuidv4(),
                    floorId: state.activeFloorId,
                    ...fixture,
                },
            ],
        })),

    removeFixture: (id) =>
        set((state) => withHistory(state, {
            fixtures: state.fixtures.filter((fixture) => fixture.id !== id),
            selection:
                state.selection?.type === 'fixture' && state.selection.id === id ? null : state.selection,
        })),

    addZone: (zoneInput) =>
        set((state) => withHistory(state, {
            zones: [
                ...state.zones,
                createZoneEntry(zoneInput, state.activeFloorId, state.zones.length + 1),
            ],
        })),

    updateZone: (id, updates) =>
        set((state) => withHistory(state, {
            zones: state.zones.map((zone) => (zone.id === id ? { ...zone, ...updates } : zone)),
        })),

    removeZone: (id) =>
        set((state) => withHistory(state, {
            zones: state.zones.filter((zone) => zone.id !== id),
            selection: state.selection?.type === 'zone' && state.selection.id === id ? null : state.selection,
        })),

    serializeLayout: () => {
        const state = get();
        return {
            floors: state.floors,
            activeFloorId: state.activeFloorId,
            objects: state.objects,
            items: state.items,
            walls: state.walls,
            fixtures: state.fixtures,
            zones: state.zones,
        };
    },

    loadLayout: (layout = {}) =>
        set(() => {
            const floors = Array.isArray(layout.floors) && layout.floors.length > 0
                ? layout.floors
                : [initialFloor];
            const activeFloorId = layout.activeFloorId || floors[0].id;
            return {
                floors,
                activeFloorId,
                objects: Array.isArray(layout.objects) ? layout.objects : [],
                items: Array.isArray(layout.items) ? layout.items : [],
                walls: Array.isArray(layout.walls) ? layout.walls : [],
                fixtures: Array.isArray(layout.fixtures) ? layout.fixtures : [],
                zones: Array.isArray(layout.zones) ? layout.zones : [],
                selection: null,
                mode: 'view',
                activeTool: 'pointer',
                placementItem: null,
                historyPast: [],
                historyFuture: [],
            };
        }),

    setSelection: (selection) => set({ selection }),
    setMode: (mode) => set({ mode }),
    setActiveTool: (activeTool) => set({ activeTool }),
    setPlacementItem: (placementItem) => set({ placementItem }),

    beginInteraction: () =>
        set((state) => {
            if (state.interactionActive) return state;
            return {
                interactionActive: true,
                historyPast: [...state.historyPast, snapshotState(state)].slice(-HISTORY_LIMIT),
                historyFuture: [],
            };
        }),

    endInteraction: () =>
        set((state) => (state.interactionActive ? { interactionActive: false } : state)),

    undo: () =>
        set((state) => {
            if (state.historyPast.length === 0) return state;
            const previous = state.historyPast[state.historyPast.length - 1];
            const current = snapshotState(state);
            return {
                ...previous,
                historyPast: state.historyPast.slice(0, -1),
                historyFuture: [current, ...state.historyFuture].slice(0, HISTORY_LIMIT),
                interactionActive: false,
            };
        }),

    redo: () =>
        set((state) => {
            if (state.historyFuture.length === 0) return state;
            const next = state.historyFuture[0];
            const current = snapshotState(state);
            return {
                ...next,
                historyPast: [...state.historyPast, current].slice(-HISTORY_LIMIT),
                historyFuture: state.historyFuture.slice(1),
                interactionActive: false,
            };
        }),

    canUndo: () => get().historyPast.length > 0,
    canRedo: () => get().historyFuture.length > 0,
}));
