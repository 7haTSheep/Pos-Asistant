import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useStore } from '../../store/store';
import { Pencil, Eye, Building2, Plus, Trash2 } from 'lucide-react';
import { LayoutManager } from './LayoutManager';

const CATALOG_GROUPS = {
    storage: [
        { id: 'storage_shelf', label: 'Storage Shelf', kind: 'object', type: 'storage_shelf' },
        { id: 'pallet_rack', label: 'Pallet Rack', kind: 'object', type: 'pallet_rack' },
        { id: 'bin_rack', label: 'Bin Rack', kind: 'object', type: 'bin_rack' },
        { id: 'cantilever_rack', label: 'Cantilever Rack', kind: 'object', type: 'cantilever_rack' },
        { id: 'pallet_stack', label: 'Pallet Stack', kind: 'object', type: 'pallet_stack' },
    ],
    cold_chain: [
        { id: 'walk_in_refrigerator', label: 'Walk-in Refrigerator', kind: 'object', type: 'walk_in_refrigerator' },
        { id: 'walk_in_freezer', label: 'Walk-in Freezer', kind: 'object', type: 'walk_in_freezer' },
        { id: 'cold_room', label: 'Cold Room', kind: 'object', type: 'cold_room' },
        { id: 'chiller_unit', label: 'Chiller Unit', kind: 'object', type: 'chiller_unit' },
    ],
    handling: [
        { id: 'forklift_bay', label: 'Forklift Bay', kind: 'object', type: 'forklift_bay' },
        { id: 'loading_dock', label: 'Loading Dock', kind: 'object', type: 'loading_dock' },
        { id: 'conveyor', label: 'Conveyor', kind: 'object', type: 'conveyor' },
        { id: 'packing_table', label: 'Packing Table', kind: 'object', type: 'packing_table' },
        { id: 'sort_station', label: 'Sort Station', kind: 'object', type: 'sort_station' },
    ],
    safety_utility: [
        { id: 'fire_extinguisher', label: 'Fire Extinguisher', kind: 'object', type: 'fire_extinguisher' },
        { id: 'first_aid_station', label: 'First Aid Station', kind: 'object', type: 'first_aid_station' },
        { id: 'electrical_panel', label: 'Electrical Panel', kind: 'object', type: 'electrical_panel' },
        { id: 'charging_station', label: 'Charging Station', kind: 'object', type: 'charging_station' },
    ],
    structure: [
        { id: 'wall', label: 'Wall', kind: 'wall', length: 6, thickness: 0.35, height: 1 },
    ],
    doors_windows: [
        { id: 'door', label: 'Door', kind: 'fixture', type: 'door', width: 1.2 },
        { id: 'window', label: 'Window', kind: 'fixture', type: 'window', width: 1.6 },
        { id: 'opening', label: 'Opening', kind: 'fixture', type: 'opening', width: 1.2 },
    ],
};

export const Sidebar = () => {
    const warehouseApiUrl = import.meta.env.VITE_WAREHOUSE_API_URL || 'http://localhost:8000';
    const floors = useStore((state) => state.floors);
    const activeFloorId = useStore((state) => state.activeFloorId);
    const addFloor = useStore((state) => state.addFloor);
    const updateFloor = useStore((state) => state.updateFloor);
    const removeFloor = useStore((state) => state.removeFloor);
    const setActiveFloor = useStore((state) => state.setActiveFloor);

    const selection = useStore((state) => state.selection);
    const objects = useStore((state) => state.objects);
    const walls = useStore((state) => state.walls);
    const fixtures = useStore((state) => state.fixtures);
    const items = useStore((state) => state.items);
    const removeObject = useStore((state) => state.removeObject);
    const updateObject = useStore((state) => state.updateObject);
    const scanItemToSlot = useStore((state) => state.scanItemToSlot);
    const removeItem = useStore((state) => state.removeItem);
    const clearFloorWalls = useStore((state) => state.clearFloorWalls);
    const removeWall = useStore((state) => state.removeWall);
    const updateWall = useStore((state) => state.updateWall);
    const removeFixture = useStore((state) => state.removeFixture);
    const setPlacementItem = useStore((state) => state.setPlacementItem);
    const activeTool = useStore((state) => state.activeTool);
    const setActiveTool = useStore((state) => state.setActiveTool);
    const addZone = useStore((state) => state.addZone);
    const removeZone = useStore((state) => state.removeZone);
    const zones = useStore((state) => state.zones);

    const mode = useStore((state) => state.mode);
    const setMode = useStore((state) => state.setMode);

    const [floorName, setFloorName] = useState('');
    const [scanCode, setScanCode] = useState('');
    const [slotRow, setSlotRow] = useState(1);
    const [slotCol, setSlotCol] = useState(1);
    const [slotLayer, setSlotLayer] = useState(1);
    const [scanQty, setScanQty] = useState(1);
    const [catalogGroup, setCatalogGroup] = useState('storage');
    const [syncEnabled, setSyncEnabled] = useState(true);
    const [syncStatus, setSyncStatus] = useState('idle');
    const lastEventIdRef = useRef(0);
    const syncReadyRef = useRef(false);
    const [zoneName, setZoneName] = useState('New Zone');
    const [zoneRowMin, setZoneRowMin] = useState(1);
    const [zoneRowMax, setZoneRowMax] = useState(2);
    const [zoneColMin, setZoneColMin] = useState(1);
    const [zoneColMax, setZoneColMax] = useState(2);
    const [zoneLayerMin, setZoneLayerMin] = useState(1);
    const [zoneLayerMax, setZoneLayerMax] = useState(1);

    const isEditMode = mode === 'edit';
    const activeFloor = floors.find((floor) => floor.id === activeFloorId) || null;

    const selectedObject = selection?.type === 'object'
        ? objects.find((item) => item.id === selection.id)
        : null;

    const selectedWall = selection?.type === 'wall'
        ? walls.find((wall) => wall.id === selection.id)
        : null;
    const selectedFixture = selection?.type === 'fixture'
        ? fixtures.find((fixture) => fixture.id === selection.id)
        : null;

    const visibleObjects = useMemo(
        () => objects.filter((obj) => obj.floorId === activeFloorId),
        [objects, activeFloorId],
    );

    const selectedItems = useMemo(
        () => items
            .filter((item) => selectedObject && item.objectId === selectedObject.id)
            .sort((a, b) => b.updatedAt - a.updatedAt),
        [items, selectedObject],
    );

    const visibleWalls = useMemo(
        () => walls.filter((wall) => wall.floorId === activeFloorId),
        [walls, activeFloorId],
    );

    const floorZones = useMemo(
        () => zones.filter((zone) => zone.floorId === activeFloorId),
        [zones, activeFloorId],
    );

    const handleAddZone = () => {
        addZone({
            name: zoneName || `Zone ${floorZones.length + 1}`,
            rowMin: Math.max(1, Math.floor(zoneRowMin)),
            rowMax: Math.max(1, Math.floor(zoneRowMax)),
            colMin: Math.max(1, Math.floor(zoneColMin)),
            colMax: Math.max(1, Math.floor(zoneColMax)),
            layerMin: Math.max(1, Math.floor(zoneLayerMin)),
            layerMax: Math.max(1, Math.floor(zoneLayerMax)),
        });
        setZoneName(`Zone ${floorZones.length + 2}`);
    };

    const catalogItems = CATALOG_GROUPS[catalogGroup] || [];

    const toggleMode = () => {
        setMode(isEditMode ? 'view' : 'edit');
    };

    const formatCoord = (val) => typeof val === 'number' ? val.toFixed(1) : '--';

    const updateDimension = (key, value) => {
        if (!activeFloor) return;
        const parsed = Math.max(10, Number(value) || 10);
        updateFloor(activeFloor.id, { dimensions: { [key]: parsed } });
    };

    const updateFloorGrid = (key, value) => {
        if (!activeFloor) return;
        if (key === 'visible') {
            updateFloor(activeFloor.id, { floorGrid: { visible: Boolean(value) } });
            return;
        }

        const parsed = Math.max(0.5, Number(value) || 1);
        updateFloor(activeFloor.id, { floorGrid: { [key]: parsed } });
    };

    const adjustSizeAxis = (axis, diff) => {
        if (!selectedObject) return;
        const newSize = [...selectedObject.size];
        newSize[axis] = Math.max(0.5, newSize[axis] + diff);
        updateObject(selectedObject.id, { size: newSize });
    };

    const adjustStorageGrid = (key, diff) => {
        if (!selectedObject) return;
        const current = selectedObject.grid?.[key] || 1;
        updateObject(selectedObject.id, {
            grid: {
                ...selectedObject.grid,
                [key]: Math.max(1, current + diff),
            },
        });
    };

    const submitScan = (event) => {
        event.preventDefault();
        if (!selectedObject || !scanCode.trim()) return;

        scanItemToSlot(
            selectedObject.id,
            { row: slotRow, col: slotCol, layer: slotLayer },
            scanCode,
            scanQty,
            { name: scanCode.trim() },
        );
        setScanCode('');
    };

    const updateSelectedWallField = (key, value, min, fallback) => {
        if (!selectedWall) return;
        const parsed = Number(value);
        const nextValue = Number.isFinite(parsed) ? Math.max(min, parsed) : fallback;
        updateWall(selectedWall.id, { [key]: nextValue });
    };

    const onCatalogDragStart = (event, item) => {
        event.dataTransfer.effectAllowed = 'copy';
        event.dataTransfer.setData('application/x-warehouse-catalog-item', JSON.stringify(item));
        setPlacementItem(item);
    };

    useEffect(() => {
        let cancelled = false;
        let intervalId = null;

        const fetchLatestCursor = async () => {
            setSyncStatus('connecting');
            try {
                const response = await fetch(`${warehouseApiUrl}/warehouse/scan-events?after_id=0&limit=1`);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                const payload = await response.json();
                if (cancelled) return;
                lastEventIdRef.current = Number(payload.latest_id || 0);
                syncReadyRef.current = true;
                setSyncStatus('listening');
            } catch {
                if (!cancelled) {
                    setSyncStatus('error');
                }
            }
        };

        const poll = async () => {
            if (!syncReadyRef.current) return;
            try {
                const response = await fetch(
                    `${warehouseApiUrl}/warehouse/scan-events?after_id=${lastEventIdRef.current}&limit=100`,
                );
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                const payload = await response.json();
                const events = Array.isArray(payload.events) ? payload.events : [];

                if (events.length > 0) {
                    events.forEach((scanEvent) => {
                        scanItemToSlot(
                            scanEvent.object_id,
                            scanEvent.slot,
                            scanEvent.barcode,
                            scanEvent.quantity,
                            {
                                externalEventId: scanEvent.id,
                                sourceDevice: scanEvent.source_device || 'mobile',
                            },
                        );
                    });
                }

                lastEventIdRef.current = Number(payload.latest_id || lastEventIdRef.current);
                setSyncStatus('listening');
            } catch {
                setSyncStatus('error');
            }
        };

        if (syncEnabled) {
            fetchLatestCursor();
            intervalId = window.setInterval(poll, 3000);
        } else {
            syncReadyRef.current = false;
            setSyncStatus('paused');
        }

        return () => {
            cancelled = true;
            if (intervalId) {
                window.clearInterval(intervalId);
            }
        };
    }, [syncEnabled, warehouseApiUrl, scanItemToSlot]);

    return (
        <div className="sidebar">
            <h1 className="text-xl font-bold mb-1">Warehouse Planner</h1>
            <p className="text-xs text-gray-400 mb-4">Floor layout + storage slot mapping</p>

            <div className="mb-6 border border-gray-700 rounded-lg p-3">
                <h2 className="text-sm uppercase text-gray-400 mb-2 font-semibold flex items-center gap-2">
                    <Building2 size={14} /> Floors
                </h2>

                <div className="space-y-2 mb-3">
                    {floors.map((floor) => (
                        <button
                            key={floor.id}
                            onClick={() => setActiveFloor(floor.id)}
                            className={`w-full text-left px-2 py-2 rounded text-sm transition ${activeFloorId === floor.id ? 'bg-blue-500/20 border border-blue-400/40' : 'bg-gray-700 hover:bg-gray-600'
                                }`}
                        >
                            {floor.name}
                        </button>
                    ))}
                </div>

                <div className="flex gap-2 mb-2">
                    <input
                        value={floorName}
                        onChange={(event) => setFloorName(event.target.value)}
                        placeholder="New floor name"
                        className="flex-1 bg-gray-700 rounded px-2 py-1 text-sm outline-none"
                    />
                    <button
                        onClick={() => {
                            addFloor(floorName);
                            setFloorName('');
                        }}
                        className="bg-blue-600 hover:bg-blue-500 rounded px-3 py-1"
                        title="Add floor"
                    >
                        <Plus size={14} />
                    </button>
                </div>

                {activeFloor && (
                    <>
                        <input
                            value={activeFloor.name}
                            onChange={(event) => updateFloor(activeFloor.id, { name: event.target.value })}
                            className="w-full bg-gray-700 rounded px-2 py-1 text-sm mb-2 outline-none"
                        />

                        <div className="grid grid-cols-2 gap-2 mb-2">
                            <label className="text-xs text-gray-400">
                                Width
                                <input
                                    type="number"
                                    min={10}
                                    step={1}
                                    value={activeFloor.dimensions.width}
                                    onChange={(event) => updateDimension('width', event.target.value)}
                                    className="w-full mt-1 bg-gray-700 rounded px-2 py-1 text-sm outline-none"
                                />
                            </label>
                            <label className="text-xs text-gray-400">
                                Depth
                                <input
                                    type="number"
                                    min={10}
                                    step={1}
                                    value={activeFloor.dimensions.depth}
                                    onChange={(event) => updateDimension('depth', event.target.value)}
                                    className="w-full mt-1 bg-gray-700 rounded px-2 py-1 text-sm outline-none"
                                />
                            </label>
                        </div>

                        <div className="grid grid-cols-2 gap-2 items-end mb-2">
                            <label className="text-xs text-gray-400">
                                Floor grid cell
                                <input
                                    type="number"
                                    min={0.5}
                                    step={0.5}
                                    value={activeFloor.floorGrid.cellSize}
                                    onChange={(event) => updateFloorGrid('cellSize', event.target.value)}
                                    className="w-full mt-1 bg-gray-700 rounded px-2 py-1 text-sm outline-none"
                                />
                            </label>
                            <label className="flex items-center gap-2 text-xs text-gray-300 pb-1">
                                <input
                                    type="checkbox"
                                    checked={Boolean(activeFloor.floorGrid.visible)}
                                    onChange={(event) => updateFloorGrid('visible', event.target.checked)}
                                />
                                Show floor grid
                            </label>
                        </div>

                        <button
                            disabled={floors.length === 1}
                            onClick={() => removeFloor(activeFloor.id)}
                            className="w-full text-sm flex items-center justify-center gap-2 bg-red-600/80 hover:bg-red-500 disabled:opacity-40 disabled:cursor-not-allowed rounded py-1"
                        >
                            <Trash2 size={14} /> Delete Floor
                        </button>
                    </>
                )}
            </div>

            <div className="mb-6 border border-gray-700 rounded-lg p-3">
                <h2 className="text-sm uppercase text-gray-400 mb-2 font-semibold">Catalog</h2>
                <select
                    value={catalogGroup}
                    onChange={(event) => setCatalogGroup(event.target.value)}
                    className="w-full mb-2"
                >
                    <option value="storage">Storage</option>
                    <option value="cold_chain">Cold Chain</option>
                    <option value="handling">Handling</option>
                    <option value="safety_utility">Safety & Utility</option>
                    <option value="structure">Structure</option>
                    <option value="doors_windows">Doors & Windows</option>
                </select>
                <div className="catalog-grid">
                    {catalogItems.map((item) => (
                        <button
                            key={item.id}
                            type="button"
                            draggable
                            onDragStart={(event) => onCatalogDragStart(event, item)}
                            onClick={() => {
                                setMode('edit');
                                setPlacementItem(item);
                            }}
                            className="catalog-tile"
                            title="Drag onto floor"
                        >
                            {item.label}
                        </button>
                    ))}
                </div>
                <p className="text-xs text-gray-500 mt-2">Drag items onto the floor to place them.</p>
            </div>

            <div>
                <LayoutManager apiUrl={warehouseApiUrl} />
            </div>

            <div>
                <h2>Zones</h2>
                <div className="space-y-2">
                    <input
                        value={zoneName}
                        onChange={(event) => setZoneName(event.target.value)}
                        placeholder="Zone name"
                    />
                    <div className="grid grid-cols-2 gap-2">
                        <input
                            type="number"
                            min={1}
                            value={zoneRowMin}
                            onChange={(event) => setZoneRowMin(Number(event.target.value) || 1)}
                            placeholder="Row min"
                        />
                        <input
                            type="number"
                            min={1}
                            value={zoneRowMax}
                            onChange={(event) => setZoneRowMax(Number(event.target.value) || zoneRowMin)}
                            placeholder="Row max"
                        />
                        <input
                            type="number"
                            min={1}
                            value={zoneColMin}
                            onChange={(event) => setZoneColMin(Number(event.target.value) || 1)}
                            placeholder="Column min"
                        />
                        <input
                            type="number"
                            min={1}
                            value={zoneColMax}
                            onChange={(event) => setZoneColMax(Number(event.target.value) || zoneColMin)}
                            placeholder="Column max"
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                        <input
                            type="number"
                            min={1}
                            value={zoneLayerMin}
                            onChange={(event) => setZoneLayerMin(Number(event.target.value) || 1)}
                            placeholder="Layer min"
                        />
                        <input
                            type="number"
                            min={1}
                            value={zoneLayerMax}
                            onChange={(event) => setZoneLayerMax(Number(event.target.value) || zoneLayerMin)}
                            placeholder="Layer max"
                        />
                    </div>
                    <button
                        type="button"
                        onClick={handleAddZone}
                    >
                        Save Zone
                    </button>
                </div>
                <div className="mt-3 space-y-1">
                    {floorZones.length === 0 && <p className="text-xs text-gray-400">No zones yet.</p>}
                    {floorZones.map((zone) => (
                        <div key={zone.id} className="flex items-center justify-between gap-2">
                            <div>
                                <p className="text-sm font-semibold">{zone.name}</p>
                                <p className="text-xs text-gray-400">
                                    Rows {zone.rowMin}-{zone.rowMax}, Cols {zone.colMin}-{zone.colMax}
                                </p>
                            </div>
                            <button type="button" onClick={() => removeZone(zone.id)}>Delete</button>
                        </div>
                    ))}
                </div>
            </div>

            <div className="mb-6 border border-gray-700 rounded-lg p-3">
                <h2 className="text-sm uppercase text-gray-400 mb-2 font-semibold">Mobile Sync</h2>
                <p className="text-xs text-gray-500 mb-2">API: {warehouseApiUrl}</p>
                <label className="flex items-center gap-2 text-sm mb-2">
                    <input
                        type="checkbox"
                        checked={syncEnabled}
                        onChange={(event) => setSyncEnabled(event.target.checked)}
                    />
                    Listen for mobile scans
                </label>
                <p className={`text-xs ${syncStatus === 'error'
                        ? 'text-red-300'
                        : syncStatus === 'listening'
                            ? 'text-emerald-300'
                            : 'text-gray-400'
                    }`}
                >
                    Status: {syncStatus}
                </p>
            </div>

            <div className="mb-6 border border-gray-700 rounded-lg p-3">
                <h2 className="text-sm uppercase text-gray-400 mb-2 font-semibold">Floor Summary</h2>
                <p className="text-xs text-gray-500">Objects on this floor: {visibleObjects.length}</p>
                <p className="text-xs text-gray-500">Walls on this floor: {visibleWalls.length}</p>
            </div>

            <div className="mb-6 border border-gray-700 rounded-lg p-3">
                <h2 className="text-sm uppercase text-gray-400 mb-2 font-semibold">Walls</h2>
                <p className="text-xs text-gray-500 mb-2">Walls on this floor: {visibleWalls.length}</p>
                <div className="grid grid-cols-2 gap-2 mb-2">
                    <button
                        onClick={() => {
                            setMode('edit');
                            setActiveTool('pencil');
                        }}
                        className={activeTool === 'pencil' ? 'is-wall-tool' : ''}
                    >
                        Pencil
                    </button>
                    <button
                        onClick={() => setActiveTool('pointer')}
                        className={activeTool === 'pointer' ? 'is-select-tool' : ''}
                    >
                        Pointer
                    </button>
                </div>
                <button
                    onClick={() => {
                        setMode('edit');
                        setActiveTool('eraser');
                    }}
                    className={`w-full mb-2 ${activeTool === 'eraser' ? 'is-eraser-tool' : ''}`}
                >
                    Eraser
                </button>
                <button
                    disabled={!activeFloor || visibleWalls.length === 0}
                    onClick={() => activeFloor && clearFloorWalls(activeFloor.id)}
                    className="w-full"
                >
                    Clear Walls On Floor
                </button>
            </div>

            {selectedObject && (
                <div className="border-t border-gray-700 pt-4">
                    <h2 className="text-sm uppercase text-gray-400 mb-3 font-semibold">Selected Object</h2>
                    <div className="space-y-3 text-sm">
                        <div className="flex justify-between">
                            <span className="text-gray-400">Type</span>
                            <span className="capitalize">{selectedObject.type}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-400">ID</span>
                            <span className="font-mono text-xs">{selectedObject.id.slice(0, 8)}</span>
                        </div>

                        <div>
                            <span className="text-gray-400 text-xs block mb-1">Position</span>
                            <div className="grid grid-cols-3 gap-1">
                                {['X', 'Y', 'Z'].map((axis, index) => (
                                    <div key={axis} className="bg-gray-700/50 rounded px-2 py-1 text-center">
                                        <span className="text-gray-500 text-[10px] block">{axis}</span>
                                        <span className="text-xs font-mono">{formatCoord(selectedObject.position?.[index])}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <button
                            onClick={toggleMode}
                            className={`w-full flex items-center justify-center gap-2 py-2 px-4 rounded-lg font-semibold text-sm transition-all ${isEditMode
                                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                                    : 'bg-gray-700 text-gray-300 border border-gray-600 hover:bg-gray-600'
                                }`}
                        >
                            {isEditMode ? <Pencil size={16} /> : <Eye size={16} />}
                            {isEditMode ? 'Editing' : 'Edit Item'}
                            <span className={`ml-auto w-2 h-2 rounded-full ${isEditMode ? 'bg-emerald-400 animate-pulse' : 'bg-gray-500'}`} />
                        </button>

                        {isEditMode && (
                            <div>
                                <span className="text-gray-400 text-xs block mb-1">Size (W/H/D)</span>
                                {['W', 'H', 'D'].map((label, axis) => (
                                    <div key={label} className="flex items-center justify-between mb-1">
                                        <span className="text-gray-500 text-xs w-4">{label}</span>
                                        <div className="flex items-center gap-1">
                                            <button
                                                onClick={() => adjustSizeAxis(axis, -0.5)}
                                                className="w-6 h-6 bg-gray-700 hover:bg-gray-600 rounded text-xs"
                                            >-</button>
                                            <span className="text-xs font-mono w-8 text-center">{formatCoord(selectedObject.size?.[axis])}</span>
                                            <button
                                                onClick={() => adjustSizeAxis(axis, 0.5)}
                                                className="w-6 h-6 bg-gray-700 hover:bg-gray-600 rounded text-xs"
                                            >+</button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className="border border-gray-700 rounded p-2">
                            <span className="text-gray-400 text-xs block mb-1">Object Storage Grid (Rows/Cols/Layers)</span>
                            <div className="space-y-1">
                                {[
                                    { key: 'rows', label: 'Rows' },
                                    { key: 'cols', label: 'Cols' },
                                    { key: 'layers', label: 'Layers' },
                                ].map((entry) => (
                                    <div key={entry.key} className="flex items-center justify-between">
                                        <span className="text-xs text-gray-400">{entry.label}</span>
                                        <div className="flex items-center gap-1">
                                            <button
                                                onClick={() => adjustStorageGrid(entry.key, -1)}
                                                className="w-6 h-6 bg-gray-700 hover:bg-gray-600 rounded text-xs"
                                            >-</button>
                                            <span className="w-8 text-center font-mono text-xs">{selectedObject.grid?.[entry.key] || 1}</span>
                                            <button
                                                onClick={() => adjustStorageGrid(entry.key, 1)}
                                                className="w-6 h-6 bg-gray-700 hover:bg-gray-600 rounded text-xs"
                                            >+</button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <form onSubmit={submitScan} className="border border-gray-700 rounded p-2 space-y-2">
                            <span className="text-gray-400 text-xs block">Scan Item To Slot</span>
                            <input
                                value={scanCode}
                                onChange={(event) => setScanCode(event.target.value)}
                                placeholder="Barcode / scanned code"
                                className="w-full bg-gray-700 rounded px-2 py-1 text-sm outline-none"
                            />
                            <div className="grid grid-cols-4 gap-1">
                                <input
                                    type="number"
                                    min={1}
                                    value={slotRow}
                                    onChange={(event) => setSlotRow(Number(event.target.value) || 1)}
                                    className="bg-gray-700 rounded px-2 py-1 text-xs outline-none"
                                    title="Row"
                                />
                                <input
                                    type="number"
                                    min={1}
                                    value={slotCol}
                                    onChange={(event) => setSlotCol(Number(event.target.value) || 1)}
                                    className="bg-gray-700 rounded px-2 py-1 text-xs outline-none"
                                    title="Column"
                                />
                                <input
                                    type="number"
                                    min={1}
                                    value={slotLayer}
                                    onChange={(event) => setSlotLayer(Number(event.target.value) || 1)}
                                    className="bg-gray-700 rounded px-2 py-1 text-xs outline-none"
                                    title="Layer"
                                />
                                <input
                                    type="number"
                                    min={1}
                                    value={scanQty}
                                    onChange={(event) => setScanQty(Number(event.target.value) || 1)}
                                    className="bg-gray-700 rounded px-2 py-1 text-xs outline-none"
                                    title="Quantity"
                                />
                            </div>
                            <button
                                type="submit"
                                className="w-full bg-blue-600 hover:bg-blue-500 text-white py-1.5 rounded text-sm"
                            >
                                Assign To Slot
                            </button>
                        </form>

                        <div className="border border-gray-700 rounded p-2">
                            <span className="text-gray-400 text-xs block mb-2">Items In Selected Object ({selectedItems.length})</span>
                            <div className="max-h-40 overflow-y-auto space-y-1">
                                {selectedItems.length === 0 && (
                                    <p className="text-xs text-gray-500">No items assigned yet.</p>
                                )}
                                {selectedItems.map((item) => (
                                    <div key={item.id} className="bg-gray-700/50 rounded p-2 text-xs">
                                        <div className="flex justify-between gap-2">
                                            <span className="font-mono text-gray-200">{item.barcode}</span>
                                            <button
                                                onClick={() => removeItem(item.id)}
                                                className="text-red-300 hover:text-red-200"
                                                title="Remove item"
                                            >
                                                <Trash2 size={12} />
                                            </button>
                                        </div>
                                        <p className="text-gray-400">Slot R{item.slot.row} C{item.slot.col} L{item.slot.layer}</p>
                                        <p className="text-gray-400">Qty: {item.quantity}</p>
                                        <p className="text-blue-300 font-mono">{item.locationCode}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <button
                            onClick={() => removeObject(selectedObject.id)}
                            className="w-full bg-red-500/80 hover:bg-red-500 text-white py-2 rounded transition"
                        >
                            Delete Object
                        </button>
                    </div>
                </div>
            )}

            {selectedWall && (
                <div className="border-t border-gray-700 pt-4">
                    <h2 className="text-sm uppercase text-gray-400 mb-3 font-semibold">Selected Wall</h2>
                    <div className="space-y-2 text-sm">
                        <p className="text-xs text-gray-500">
                            Start: {selectedWall.start?.[0]} , {selectedWall.start?.[1]}
                        </p>
                        <p className="text-xs text-gray-500">
                            End: {selectedWall.end?.[0]} , {selectedWall.end?.[1]}
                        </p>
                        <label className="text-xs text-gray-500">
                            Thickness
                            <input
                                type="number"
                                min={0.1}
                                step={0.05}
                                value={selectedWall.thickness ?? 0.35}
                                onChange={(event) => updateSelectedWallField('thickness', event.target.value, 0.1, 0.35)}
                                className="w-full mt-1"
                            />
                        </label>
                        <label className="text-xs text-gray-500">
                            Height
                            <input
                                type="number"
                                min={0.2}
                                step={0.1}
                                value={selectedWall.height ?? 1}
                                onChange={(event) => updateSelectedWallField('height', event.target.value, 0.2, 1)}
                                className="w-full mt-1"
                            />
                        </label>
                        <button
                            onClick={() => removeWall(selectedWall.id)}
                            className="w-full"
                        >
                            Delete Wall
                        </button>
                        <p className="text-xs text-gray-400">
                            Tip: Use Pointer to drag whole walls. Use Eraser to remove walls under the cursor.
                        </p>
                    </div>
                </div>
            )}

            {selectedFixture && (
                <div className="border-t border-gray-700 pt-4">
                    <h2 className="text-sm uppercase text-gray-400 mb-3 font-semibold">Selected Fixture</h2>
                    <div className="space-y-2 text-sm">
                        <p className="text-xs text-gray-500 capitalize">Type: {selectedFixture.type}</p>
                        <p className="text-xs text-gray-500">Width: {selectedFixture.width}</p>
                        <button
                            onClick={() => removeFixture(selectedFixture.id)}
                            className="w-full"
                        >
                            Delete Fixture
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};
