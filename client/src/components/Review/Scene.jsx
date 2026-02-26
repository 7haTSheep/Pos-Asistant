import React, { Suspense, useEffect, useCallback } from 'react';
import { Canvas } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { WarehouseFloor } from './WarehouseFloor';
import { ZoneModal } from '../UI/ZoneModal';

import { useStore } from '../../store/store';
import { Furniture } from '../Objects/Furniture';

const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
const ITEM_FOOTPRINT_SCALE = 0.32;
const warehouseApiUrl = import.meta.env.VITE_WAREHOUSE_API_URL || '';

const computeZoneMesh = (zone, floor) => {
    if (!zone || !floor) return null;
    const cellSize = Math.max(0.5, floor.floorGrid?.cellSize || 1);
    const floorWidth = Math.max(1, floor.dimensions?.width || 50);
    const floorDepth = Math.max(1, floor.dimensions?.depth || 50);

    const rowMin = Math.max(1, Math.min(zone.rowMin || 1, zone.rowMax || 1));
    const rowMax = Math.max(rowMin, zone.rowMax || rowMin);
    const colMin = Math.max(1, Math.min(zone.colMin || 1, zone.colMax || 1));
    const colMax = Math.max(colMin, zone.colMax || colMin);

    const spanRows = Math.max(1, rowMax - rowMin + 1);
    const spanCols = Math.max(1, colMax - colMin + 1);

    const centerRowIndex = ((rowMin - 1) + (rowMax - 1)) / 2;
    const centerColIndex = ((colMin - 1) + (colMax - 1)) / 2;

    const centerX = -floorWidth / 2 + cellSize / 2 + centerColIndex * cellSize;
    const centerZ = -floorDepth / 2 + cellSize / 2 + centerRowIndex * cellSize;
    const width = Math.min(floorWidth, spanCols * cellSize);
    const depth = Math.min(floorDepth, spanRows * cellSize);

    return {
        center: [centerX, 0.05, centerZ],
        size: [Math.max(cellSize, width), Math.max(cellSize, depth)],
    };
};

export const Scene = () => {
    const objects = useStore((state) => state.objects);
    const walls = useStore((state) => state.walls);
    const fixtures = useStore((state) => state.fixtures);
    const zones = useStore((state) => state.zones);
    const floors = useStore((state) => state.floors);
    const activeFloorId = useStore((state) => state.activeFloorId);
    const selection = useStore((state) => state.selection);
    const updateObject = useStore((state) => state.updateObject);
    const addObject = useStore((state) => state.addObject);
    const removeObject = useStore((state) => state.removeObject);
    const setSelection = useStore((state) => state.setSelection);
    const mode = useStore((state) => state.mode);
    const setMode = useStore((state) => state.setMode);
    const activeTool = useStore((state) => state.activeTool);
    const addWall = useStore((state) => state.addWall);
    const updateWall = useStore((state) => state.updateWall);
    const removeWall = useStore((state) => state.removeWall);
    const addFixture = useStore((state) => state.addFixture);
    const removeFixture = useStore((state) => state.removeFixture);
    const placementItem = useStore((state) => state.placementItem);
    const setPlacementItem = useStore((state) => state.setPlacementItem);
    const beginInteraction = useStore((state) => state.beginInteraction);
    const endInteraction = useStore((state) => state.endInteraction);

    const isEditMode = mode === 'edit';

    const [draggedId, setDraggedId] = React.useState(null);
    const [pencilStart, setPencilStart] = React.useState(null);
    const [activeZone, setActiveZone] = React.useState(null);
    const [pencilHover, setPencilHover] = React.useState(null);
    const [wallDrag, setWallDrag] = React.useState(null);
    const [fixturePreview, setFixturePreview] = React.useState(null);
    const [rotatingObjectId, setRotatingObjectId] = React.useState(null);
    const dragOffset = React.useRef([0, 0, 0]);
    const suppressNextFloorClearRef = React.useRef(false);
    const cameraRef = React.useRef(null);
    const canvasRef = React.useRef(null);

    const activeFloor = floors.find((floor) => floor.id === activeFloorId);
    const visibleObjects = objects.filter((obj) => obj.floorId === activeFloorId);
    const visibleWalls = walls.filter((wall) => wall.floorId === activeFloorId);
    const visibleFixtures = fixtures.filter((fixture) => fixture.floorId === activeFloorId);
    const visibleZones = zones.filter((zone) => zone.floorId === activeFloorId);
    const selectedObject = selection?.type === 'object'
        ? visibleObjects.find((obj) => obj.id === selection.id)
        : null;

    const floorWidth = activeFloor?.dimensions?.width || 50;
    const floorDepth = activeFloor?.dimensions?.depth || 50;
    const cellSize = Math.max(0.5, activeFloor?.floorGrid?.cellSize || 1);
    const cameraZoom = Math.max(8, 900 / Math.max(floorWidth, floorDepth));

    const snapPoint = useCallback((point) => {
        const halfW = floorWidth / 2;
        const halfD = floorDepth / 2;

        const clampedX = Math.min(halfW, Math.max(-halfW, point.x));
        const clampedZ = Math.min(halfD, Math.max(-halfD, point.z));

        return [
            Math.round(clampedX / cellSize) * cellSize,
            Math.round(clampedZ / cellSize) * cellSize,
        ];
    }, [floorWidth, floorDepth, cellSize]);

    const toOrthogonalEnd = useCallback((start, target) => {
        const dx = target[0] - start[0];
        const dz = target[1] - start[1];
        if (Math.abs(dx) >= Math.abs(dz)) {
            return [target[0], start[1]];
        }
        return [start[0], target[1]];
    }, []);

    const nearestWallInfo = useCallback((point) => {
        let best = null;

        visibleWalls.forEach((wall) => {
            const sx = wall.start[0];
            const sz = wall.start[1];
            const ex = wall.end[0];
            const ez = wall.end[1];

            const vx = ex - sx;
            const vz = ez - sz;
            const lenSq = vx * vx + vz * vz;
            if (lenSq < 0.0001) return;

            const wx = point[0] - sx;
            const wz = point[1] - sz;
            const t = clamp((wx * vx + wz * vz) / lenSq, 0, 1);

            const px = sx + vx * t;
            const pz = sz + vz * t;
            const dx = point[0] - px;
            const dz = point[1] - pz;
            const dist = Math.hypot(dx, dz);

            if (!best || dist < best.dist) {
                best = {
                    wall,
                    t,
                    point: [px, pz],
                    dist,
                    length: Math.hypot(vx, vz),
                    angle: Math.atan2(vz, vx),
                };
            }
        });

        return best;
    }, [visibleWalls]);

    const stageFixturePreview = useCallback((point) => {
        if (!placementItem || placementItem.kind !== 'fixture') {
            setFixturePreview(null);
            return;
        }

        const nearest = nearestWallInfo(point);
        if (!nearest || nearest.dist > Math.max(1.2, cellSize * 1.5)) {
            setFixturePreview(null);
            return;
        }

        const width = Number(placementItem.width) || 1.2;
        const halfRatio = clamp((width / Math.max(nearest.length, 0.001)) / 2, 0, 0.45);
        const t = clamp(nearest.t, halfRatio, 1 - halfRatio);

        setFixturePreview({
            wallId: nearest.wall.id,
            type: placementItem.type,
            width,
            t,
            angle: nearest.angle,
            point: [
                nearest.wall.start[0] + (nearest.wall.end[0] - nearest.wall.start[0]) * t,
                nearest.wall.start[1] + (nearest.wall.end[1] - nearest.wall.start[1]) * t,
            ],
        });
    }, [placementItem, nearestWallInfo, cellSize]);

    const placeFixtureAtPoint = useCallback((point, item) => {
        const nearest = nearestWallInfo(point);
        if (!nearest) return false;

        if (nearest.dist > Math.max(1.2, cellSize * 1.5)) return false;

        const width = Number(item.width) || 1.2;
        const halfRatio = clamp((width / Math.max(nearest.length, 0.001)) / 2, 0, 0.45);
        const t = clamp(nearest.t, halfRatio, 1 - halfRatio);

        addFixture({
            type: item.type,
            wallId: nearest.wall.id,
            width,
            t,
            side: 1,
        });
        return true;
    }, [addFixture, nearestWallInfo, cellSize]);

    const getFloorPointFromScreen = useCallback((clientX, clientY) => {
        const camera = cameraRef.current;
        const canvas = canvasRef.current;
        if (!camera || !canvas) return null;

        const rect = canvas.getBoundingClientRect();
        const ndc = new THREE.Vector2(
            ((clientX - rect.left) / rect.width) * 2 - 1,
            -((clientY - rect.top) / rect.height) * 2 + 1,
        );

        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(ndc, camera);

        const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
        const hit = new THREE.Vector3();
        const didHit = raycaster.ray.intersectPlane(plane, hit);
        if (!didHit) return null;

        return snapPoint(hit);
    }, [snapPoint]);

    const handleCatalogDrop = (event) => {
        event.preventDefault();
        const raw = event.dataTransfer.getData('application/x-warehouse-catalog-item');
        if (!raw) return;

        let item = null;
        try {
            item = JSON.parse(raw);
        } catch {
            return;
        }

        const point = getFloorPointFromScreen(event.clientX, event.clientY);
        if (!point || !item) return;

        setMode('edit');

        if (item.kind === 'wall') {
            const length = Math.max(cellSize, Number(item.length) || 4);
            const halfLength = length / 2;
            const halfW = floorWidth / 2;
            const startX = Math.max(-halfW, point[0] - halfLength);
            const endX = Math.min(halfW, point[0] + halfLength);
            addWall([startX, point[1]], [endX, point[1]], {
                thickness: Number(item.thickness) || 0.35,
                height: Number(item.height) || 1,
            });
            setPlacementItem(null);
            return;
        }

        if (item.kind === 'fixture') {
            const placed = placeFixtureAtPoint(point, item);
            setPlacementItem(placed ? null : item);
            return;
        }

        if (item.kind === 'object' && item.type) {
            if (item.placeOn === 'desk') {
                const nearestDesk = visibleObjects
                    .filter((obj) => obj.type === 'desk')
                    .map((obj) => ({
                        obj,
                        dist: Math.hypot(point[0] - obj.position[0], point[1] - obj.position[2]),
                    }))
                    .sort((a, b) => a.dist - b.dist)[0];

                if (nearestDesk && nearestDesk.dist <= 3) {
                    addObject(item.type, [nearestDesk.obj.position[0], 2, nearestDesk.obj.position[2]]);
                    setPlacementItem(null);
                    return;
                }
            }

            addObject(item.type, [point[0], 1, point[1]]);
            setPlacementItem(null);
        }
    };

    const handleObjectDragStart = (id, point, currentPos) => {
        if (!currentPos || activeTool !== 'pointer') return;
        suppressNextFloorClearRef.current = true;
        if (!isEditMode || !(selection?.type === 'object' && selection.id === id)) {
            setSelection({ type: 'object', id });
            return;
        }

        dragOffset.current = [point.x - currentPos[0], 0, point.z - currentPos[2]];
        beginInteraction();
        setDraggedId(id);
        setSelection({ type: 'object', id });
    };

    const handleRotateStart = (event, objectId) => {
        event.stopPropagation();
        if (!isEditMode || activeTool !== 'pointer') return;
        beginInteraction();
        setRotatingObjectId(objectId);
    };

    const startWallDrag = (event, wall) => {
        event.stopPropagation();
        if (!isEditMode || activeTool !== 'pointer') return;

        const dx = wall.end[0] - wall.start[0];
        const dz = wall.end[1] - wall.start[1];
        const orientation = Math.abs(dx) >= Math.abs(dz) ? 'horizontal' : 'vertical';

        setSelection({ type: 'wall', id: wall.id });
        beginInteraction();
        setWallDrag({
            wallId: wall.id,
            orientation,
            anchor: snapPoint(event.point),
            originalStart: wall.start,
            originalEnd: wall.end,
        });
    };

    const eraseWall = (event, wallId) => {
        event.stopPropagation();
        if (!isEditMode || activeTool !== 'eraser') return;
        removeWall(wallId);
    };

    const maybeEraseOnHover = (event, wallId) => {
        if (!isEditMode || activeTool !== 'eraser') return;
        if (event.buttons === 1) {
            event.stopPropagation();
            removeWall(wallId);
        }
    };

    const handleFloorMove = (point) => {
        if (rotatingObjectId && isEditMode) {
            const obj = visibleObjects.find((item) => item.id === rotatingObjectId);
            if (!obj) return;
            const dx = point.x - obj.position[0];
            const dz = point.z - obj.position[2];
            const nextAngle = Math.atan2(dz, dx);
            updateObject(rotatingObjectId, { rotation: [0, -nextAngle, 0] }, { skipHistory: true });
            return;
        }

        if (placementItem?.kind === 'fixture') {
            stageFixturePreview(snapPoint(point));
        }

        if (wallDrag && isEditMode) {
            const snapped = snapPoint(point);
            const halfW = floorWidth / 2;
            const halfD = floorDepth / 2;

            if (wallDrag.orientation === 'horizontal') {
                const proposedDeltaZ = snapped[1] - wallDrag.anchor[1];
                const origZ = wallDrag.originalStart[1];
                const clampedZ = Math.min(halfD, Math.max(-halfD, origZ + proposedDeltaZ));
                const deltaZ = clampedZ - origZ;

                updateWall(wallDrag.wallId, {
                    start: [wallDrag.originalStart[0], wallDrag.originalStart[1] + deltaZ],
                    end: [wallDrag.originalEnd[0], wallDrag.originalEnd[1] + deltaZ],
                }, { skipHistory: true });
                return;
            }

            const proposedDeltaX = snapped[0] - wallDrag.anchor[0];
            const origX = wallDrag.originalStart[0];
            const clampedX = Math.min(halfW, Math.max(-halfW, origX + proposedDeltaX));
            const deltaX = clampedX - origX;

            updateWall(wallDrag.wallId, {
                start: [wallDrag.originalStart[0] + deltaX, wallDrag.originalStart[1]],
                end: [wallDrag.originalEnd[0] + deltaX, wallDrag.originalEnd[1]],
            }, { skipHistory: true });
            return;
        }

        if (draggedId) {
            const offset = dragOffset.current;
            const rawX = point.x - offset[0];
            const rawZ = point.z - offset[2];

            const obj = visibleObjects.find((o) => o.id === draggedId);
            if (obj) {
                const halfW = floorWidth / 2;
                const halfD = floorDepth / 2;
                const scaledW = clamp((obj.size?.[0] || 1) * ITEM_FOOTPRINT_SCALE, 0.2, 3.2);
                const scaledD = clamp((obj.size?.[2] || 1) * ITEM_FOOTPRINT_SCALE, 0.2, 3.2);
                const objectHalfW = scaledW / 2;
                const objectHalfD = scaledD / 2;

                const clampedX = Math.min(halfW - objectHalfW, Math.max(-halfW + objectHalfW, rawX));
                const clampedZ = Math.min(halfD - objectHalfD, Math.max(-halfD + objectHalfD, rawZ));
                const snappedX = Math.round(clampedX / cellSize) * cellSize;
                const snappedZ = Math.round(clampedZ / cellSize) * cellSize;

                updateObject(draggedId, { position: [snappedX, obj.position[1], snappedZ] }, { skipHistory: true });
            }
            return;
        }

        if (activeTool === 'pencil' && isEditMode && pencilStart) {
            setPencilHover(snapPoint(point));
        }
    };

    const handleFloorClick = (point) => {
        if (suppressNextFloorClearRef.current) {
            suppressNextFloorClearRef.current = false;
            return;
        }

        if (placementItem?.kind === 'wall') {
            const length = Math.max(cellSize, Number(placementItem.length) || 4);
            const halfLength = length / 2;
            const halfW = floorWidth / 2;
            const startX = Math.max(-halfW, point[0] - halfLength);
            const endX = Math.min(halfW, point[0] + halfLength);
            addWall([startX, point[1]], [endX, point[1]], {
                thickness: Number(placementItem.thickness) || 0.35,
                height: Number(placementItem.height) || 1,
            });
            setPlacementItem(null);
            return;
        }

        if (placementItem?.kind === 'fixture') {
            const placed = placeFixtureAtPoint(point, placementItem);
            if (placed) {
                setPlacementItem(null);
                setFixturePreview(null);
            }
            return;
        }

        if (placementItem?.kind === 'object' && placementItem.type) {
            if (placementItem.placeOn === 'desk') {
                const nearestDesk = visibleObjects
                    .filter((obj) => obj.type === 'desk')
                    .map((obj) => ({
                        obj,
                        dist: Math.hypot(point[0] - obj.position[0], point[1] - obj.position[2]),
                    }))
                    .sort((a, b) => a.dist - b.dist)[0];

                if (nearestDesk && nearestDesk.dist <= 3) {
                    addObject(placementItem.type, [nearestDesk.obj.position[0], 2, nearestDesk.obj.position[2]]);
                    setPlacementItem(null);
                    return;
                }
            }

            addObject(placementItem.type, [point[0], 1, point[1]]);
            setPlacementItem(null);
            return;
        }

        if (activeTool !== 'pencil' || !isEditMode) {
            setSelection(null);
            return;
        }

        const snapped = snapPoint(point);

        if (!pencilStart) {
            setSelection(null);
            setPencilStart(snapped);
            setPencilHover(snapped);
            return;
        }

        const alignedEnd = toOrthogonalEnd(pencilStart, snapped);
        if (pencilStart[0] === alignedEnd[0] && pencilStart[1] === alignedEnd[1]) {
            return;
        }

        addWall(pencilStart, alignedEnd);
        setPencilStart(alignedEnd);
        setPencilHover(alignedEnd);
    };

    const handleZoneClick = (zone, event) => {
        event.stopPropagation();
        if (mode !== 'view') {
            setSelection({ type: 'zone', id: zone.id });
            return;
        }
        setSelection({ type: 'zone', id: zone.id });
        setActiveZone(zone);
    };

    const handleDragEnd = useCallback(() => {
        setDraggedId(null);
        setWallDrag(null);
        setRotatingObjectId(null);
        dragOffset.current = [0, 0, 0];
        endInteraction();
    }, [endInteraction]);

    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            if (e.key === '?') return;

            if (e.key === 'Escape') {
                e.preventDefault();
                setSelection(null);
                setPencilStart(null);
                setPencilHover(null);
                setDraggedId(null);
                setWallDrag(null);
                setPlacementItem(null);
                setFixturePreview(null);
                setRotatingObjectId(null);
                endInteraction();
                return;
            }

            if (!isEditMode) return;

            if ((e.key === 'Delete' || e.key === 'Backspace') && selection?.type === 'wall') {
                e.preventDefault();
                removeWall(selection.id);
                return;
            }

            if ((e.key === 'Delete' || e.key === 'Backspace') && selection?.type === 'fixture') {
                e.preventDefault();
                removeFixture(selection.id);
                return;
            }

            if (activeTool !== 'pointer') return;

            const selectedId = selection?.type === 'object' ? selection.id : null;
            const selectedObj = selectedId ? visibleObjects.find((o) => o.id === selectedId) : null;
            if (!selectedObj) return;

            const step = e.shiftKey ? Math.max(0.1, cellSize / 5) : cellSize;
            const [px, py, pz] = selectedObj.position;

            switch (e.key) {
                case 'ArrowUp':
                    e.preventDefault();
                    updateObject(selectedId, { position: [px, py, pz - step] });
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    updateObject(selectedId, { position: [px, py, pz + step] });
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    updateObject(selectedId, { position: [px - step, py, pz] });
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    updateObject(selectedId, { position: [px + step, py, pz] });
                    break;
                case 'r':
                case 'R': {
                    e.preventDefault();
                    const [rx, ry, rz] = selectedObj.rotation;
                    updateObject(selectedId, { rotation: [rx, ry + Math.PI / 2, rz] });
                    break;
                }
                case 'Delete':
                case 'Backspace':
                    e.preventDefault();
                    removeObject(selectedId);
                    setSelection(null);
                    break;
                default:
                    break;
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [
        isEditMode,
        activeTool,
        selection,
        visibleObjects,
        updateObject,
        removeObject,
        setSelection,
        cellSize,
        removeWall,
        removeFixture,
        setPlacementItem,
        endInteraction,
    ]);

    useEffect(() => {
        const releaseDrag = () => handleDragEnd();
        window.addEventListener('pointerup', releaseDrag);
        window.addEventListener('pointercancel', releaseDrag);
        return () => {
            window.removeEventListener('pointerup', releaseDrag);
            window.removeEventListener('pointercancel', releaseDrag);
        };
    }, [handleDragEnd]);

    const previewEnd = pencilStart && pencilHover ? toOrthogonalEnd(pencilStart, pencilHover) : null;

    return (
        <div
            className="scene-root"
            onDragOver={(event) => {
                event.preventDefault();
                event.dataTransfer.dropEffect = 'copy';
            }}
            onDrop={handleCatalogDrop}
        >
            {placementItem?.kind === 'fixture' && (
                <div className="wall-draw-hint">
                    {placementItem.label}: hover near a wall and click to place.
                </div>
            )}
            {!placementItem && activeTool === 'pencil' && (
                <div className="wall-draw-hint">
                    Pencil: click to start, click again to place orthogonal segments, Esc to stop.
                </div>
            )}
            {!placementItem && activeTool === 'eraser' && (
                <div className="wall-draw-hint">
                    Eraser: click a wall or hold mouse and sweep across walls to delete.
                </div>
            )}
            {!placementItem && activeTool === 'pointer' && (
                <div className="wall-draw-hint">
                    Pointer: drag a wall to slide it (horizontal walls move vertically, vertical walls move horizontally).
                </div>
            )}

            <Canvas
                orthographic
                camera={{ position: [0, 60, 0.01], zoom: cameraZoom, near: 0.1, far: 200 }}
                onCreated={({ camera, gl }) => {
                    camera.up.set(0, 0, -1);
                    camera.lookAt(0, 0, 0);
                    camera.updateProjectionMatrix();
                    cameraRef.current = camera;
                    canvasRef.current = gl.domElement;
                }}
            >
                <color attach="background" args={['#dbe3ea']} />
                <ambientLight intensity={1} />

                <Suspense fallback={null}>
                    <WarehouseFloor
                        floor={activeFloor}
                        onDragMove={handleFloorMove}
                        onDragEnd={handleDragEnd}
                        onClickEmpty={handleFloorClick}
                    />

                    {visibleWalls.map((wall) => {
                        const dx = wall.end[0] - wall.start[0];
                        const dz = wall.end[1] - wall.start[1];
                        const length = Math.hypot(dx, dz);
                        if (length < 0.05) return null;

                        const midX = (wall.start[0] + wall.end[0]) / 2;
                        const midZ = (wall.start[1] + wall.end[1]) / 2;
                        const angle = Math.atan2(dz, dx);
                        const isSelectedWall = selection?.type === 'wall' && selection.id === wall.id;

                        return (
                            <mesh
                                key={wall.id}
                                position={[midX, (wall.height || 1) / 2, midZ]}
                                rotation={[0, -angle, 0]}
                                onClick={(event) => {
                                    event.stopPropagation();

                                    if (placementItem?.kind === 'fixture') {
                                        const snapped = snapPoint(event.point);
                                        const placed = placeFixtureAtPoint(snapped, placementItem);
                                        if (placed) {
                                            setPlacementItem(null);
                                            setFixturePreview(null);
                                        }
                                        return;
                                    }

                                    if (activeTool === 'eraser') {
                                        removeWall(wall.id);
                                    } else {
                                        setSelection({ type: 'wall', id: wall.id });
                                    }
                                }}
                                onPointerDown={(event) => {
                                    if (placementItem?.kind === 'fixture') return;
                                    if (activeTool === 'pointer') {
                                        startWallDrag(event, wall);
                                    } else if (activeTool === 'eraser') {
                                        eraseWall(event, wall.id);
                                    }
                                }}
                                onPointerEnter={(event) => maybeEraseOnHover(event, wall.id)}
                                onPointerMove={(event) => maybeEraseOnHover(event, wall.id)}
                            >
                                <boxGeometry args={[length, wall.height || 1, wall.thickness || 0.35]} />
                                <meshBasicMaterial color={isSelectedWall ? '#2563eb' : '#4b5563'} />
                            </mesh>
                        );
                    })}

                    {visibleFixtures.map((fixture) => {
                        const wall = visibleWalls.find((w) => w.id === fixture.wallId);
                        if (!wall) return null;

                        const vx = wall.end[0] - wall.start[0];
                        const vz = wall.end[1] - wall.start[1];
                        const length = Math.hypot(vx, vz);
                        if (length < 0.01) return null;

                        const t = clamp(fixture.t ?? 0.5, 0, 1);
                        const px = wall.start[0] + vx * t;
                        const pz = wall.start[1] + vz * t;
                        const angle = Math.atan2(vz, vx);
                        const width = Number(fixture.width) || 1.2;
                        const isSelected = selection?.type === 'fixture' && selection.id === fixture.id;

                        if (fixture.type === 'door') {
                            const radius = width * 0.95;
                            const arcPoints = [];
                            for (let i = 0; i <= 16; i += 1) {
                                const a = (i / 16) * (Math.PI / 2);
                                arcPoints.push([
                                    -width / 2 + Math.cos(a) * radius,
                                    0.12,
                                    Math.sin(a) * radius,
                                ]);
                            }

                            return (
                                <group
                                    key={fixture.id}
                                    position={[px, 0.1, pz]}
                                    rotation={[0, -angle, 0]}
                                    onClick={(event) => {
                                        event.stopPropagation();
                                        setSelection({ type: 'fixture', id: fixture.id });
                                    }}
                                >
                                    <Line points={[[-width / 2, 0.1, 0], [width / 2, 0.1, 0]]} color="#4b5563" lineWidth={2} />
                                    <Line points={[[-width / 2, 0.1, 0], [-width / 2 + radius, 0.1, 0]]} color="#6b7280" lineWidth={2} />
                                    <Line points={arcPoints} color="#6b7280" lineWidth={1.5} />
                                    {isSelected && (
                                        <mesh position={[0, 0.11, 0]}>
                                            <boxGeometry args={[width, 0.02, 0.08]} />
                                            <meshBasicMaterial color="#2563eb" />
                                        </mesh>
                                    )}
                                </group>
                            );
                        }

                        if (fixture.type === 'window') {
                            return (
                                <group
                                    key={fixture.id}
                                    position={[px, 0.14, pz]}
                                    rotation={[0, -angle, 0]}
                                    onClick={(event) => {
                                        event.stopPropagation();
                                        setSelection({ type: 'fixture', id: fixture.id });
                                    }}
                                >
                                    <mesh>
                                        <boxGeometry args={[width, 0.08, 0.1]} />
                                        <meshBasicMaterial color={isSelected ? '#2563eb' : '#0ea5e9'} />
                                    </mesh>
                                </group>
                            );
                        }

                        return (
                            <group
                                key={fixture.id}
                                position={[px, 0.14, pz]}
                                rotation={[0, -angle, 0]}
                                onClick={(event) => {
                                    event.stopPropagation();
                                    setSelection({ type: 'fixture', id: fixture.id });
                                }}
                            >
                                <mesh>
                                    <boxGeometry args={[width, 0.08, 0.1]} />
                                    <meshBasicMaterial color={isSelected ? '#2563eb' : '#94a3b8'} />
                                </mesh>
                            </group>
                        );
                    })}

                    {fixturePreview && (
                        <group
                            position={[fixturePreview.point[0], 0.15, fixturePreview.point[1]]}
                            rotation={[0, -fixturePreview.angle, 0]}
                        >
                            <mesh>
                                <boxGeometry args={[fixturePreview.width, 0.06, 0.08]} />
                                <meshBasicMaterial color="#16a34a" transparent opacity={0.8} />
                            </mesh>
                        </group>
                    )}

                    {pencilStart && previewEnd && (
                        <Line
                            points={[
                                [pencilStart[0], 0.7, pencilStart[1]],
                                [previewEnd[0], 0.7, previewEnd[1]],
                            ]}
                            color="#16a34a"
                            lineWidth={2}
                        />
                    )}

                    {visibleZones.map((zone) => {
                        const meshProps = computeZoneMesh(zone, activeFloor);
                        if (!meshProps) return null;
                        const isSelectedZone = selection?.type === 'zone' && selection.id === zone.id;
                        return (
                            <mesh
                                key={zone.id}
                                position={meshProps.center}
                                rotation={[-Math.PI / 2, 0, 0]}
                                onClick={(event) => handleZoneClick(zone, event)}
                            >
                                <planeGeometry args={meshProps.size} />
                                <meshBasicMaterial
                                    color={zone.color || '#f97316'}
                                    transparent
                                    opacity={isSelectedZone ? 0.65 : 0.25}
                                />
                            </mesh>
                        );
                    })}
                    {visibleObjects.map((obj) => (
                        <Furniture
                            key={obj.id}
                            {...obj}
                            isSelected={activeTool === 'pointer' && selection?.type === 'object' && selection.id === obj.id}
                            isDragged={draggedId === obj.id}
                            onDragStart={activeTool === 'pointer' ? handleObjectDragStart : undefined}
                        />
                    ))}

                    {selectedObject && activeTool === 'pointer' && isEditMode && (
                        (() => {
                            const handleOffset = Math.max(
                                0.8,
                                ((selectedObject.size?.[0] || 1) * ITEM_FOOTPRINT_SCALE) / 2 + 0.8,
                            );
                            const ox = selectedObject.position[0];
                            const oz = selectedObject.position[2];
                            const hx = ox + Math.cos(-(selectedObject.rotation?.[1] || 0)) * handleOffset;
                            const hz = oz + Math.sin(-(selectedObject.rotation?.[1] || 0)) * handleOffset;

                            return (
                                <group>
                                    <Line
                                        points={[[ox, 0.18, oz], [hx, 0.18, hz]]}
                                        color="#334155"
                                        dashed
                                        lineWidth={1}
                                    />
                                    <mesh
                                        position={[hx, 0.2, hz]}
                                        onPointerDown={(event) => handleRotateStart(event, selectedObject.id)}
                                    >
                                        <cylinderGeometry args={[0.28, 0.28, 0.06, 24]} />
                                        <meshBasicMaterial color="#0ea5e9" />
                                    </mesh>
                                </group>
                            );
                        })()
                    )}
                </Suspense>
            </Canvas>
            <ZoneModal zone={activeZone} onClose={() => setActiveZone(null)} apiUrl={warehouseApiUrl} />
        </div>
    );
};
