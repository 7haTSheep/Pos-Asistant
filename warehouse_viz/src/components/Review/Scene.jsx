import React, { Suspense, useEffect, useCallback } from 'react';
import { Canvas } from '@react-three/fiber';
import { CameraController } from './CameraController';
import { WarehouseFloor } from './WarehouseFloor';
import { Environment } from '@react-three/drei';

import { useStore } from '../../store/store';
import { Furniture } from '../Objects/Furniture';

export const Scene = () => {
    const objects = useStore((state) => state.objects);
    const selection = useStore((state) => state.selection);
    const updateObject = useStore((state) => state.updateObject);
    const removeObject = useStore((state) => state.removeObject);
    const setSelection = useStore((state) => state.setSelection);
    const mode = useStore((state) => state.mode);

    const isEditMode = mode === 'edit';

    // Drag state
    const [draggedId, setDraggedId] = React.useState(null);
    const dragOffset = React.useRef([0, 0, 0]);

    // --- Drag handlers (only active in edit mode) ---
    const handleDragStart = (id, point, currentPos) => {
        if (!isEditMode || !currentPos) return;

        dragOffset.current = [point.x - currentPos[0], 0, point.z - currentPos[2]];
        setDraggedId(id);
        setSelection({ type: 'object', id });
    };

    const handleDragMove = (point) => {
        if (!draggedId || !isEditMode) return;

        const offset = dragOffset.current;
        const newX = point.x - offset[0];
        const newZ = point.z - offset[2];

        const obj = objects.find(o => o.id === draggedId);
        if (obj) {
            updateObject(draggedId, { position: [newX, obj.position[1], newZ] });
        }
    };

    const handleDragEnd = () => {
        setDraggedId(null);
        dragOffset.current = [0, 0, 0];
    };

    // --- Keyboard shortcuts ---
    const handleKeyDown = useCallback((e) => {
        // Skip if typing in an input
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        // ? key is handled by ControlsHelp component
        if (e.key === '?') return;

        if (!isEditMode) return;

        const selectedId = selection?.type === 'object' ? selection.id : null;
        const selectedObj = selectedId ? objects.find(o => o.id === selectedId) : null;

        if (!selectedObj) {
            // Only Escape works without selection
            if (e.key === 'Escape') {
                setSelection(null);
            }
            return;
        }

        const step = e.shiftKey ? 0.1 : 0.5;
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
            case 'R':
                e.preventDefault();
                const [rx, ry, rz] = selectedObj.rotation;
                updateObject(selectedId, { rotation: [rx, ry + Math.PI / 2, rz] });
                break;
            case 'Delete':
            case 'Backspace':
                e.preventDefault();
                removeObject(selectedId);
                setSelection(null);
                break;
            case 'Escape':
                e.preventDefault();
                setSelection(null);
                break;
            default:
                break;
        }
    }, [isEditMode, selection, objects, updateObject, removeObject, setSelection]);

    useEffect(() => {
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [handleKeyDown]);

    return (
        <div className="h-screen w-full bg-gray-900">
            <Canvas shadows camera={{ position: [10, 15, 10], fov: 50 }}>
                <fog attach="fog" args={['#171717', 10, 50]} />
                <ambientLight intensity={0.5} />
                <directionalLight
                    position={[10, 20, 10]}
                    intensity={1}
                    castShadow
                    shadow-mapSize={[2048, 2048]}
                />

                <Suspense fallback={null}>
                    <WarehouseFloor
                        onDragMove={handleDragMove}
                        onDragEnd={handleDragEnd}
                        onClickEmpty={() => setSelection(null)}
                    />
                    <CameraController enabled={!isEditMode} />
                    <Environment preset="city" />

                    {objects.map((obj) => (
                        <Furniture
                            key={obj.id}
                            {...obj}
                            isSelected={selection?.type === 'object' && selection.id === obj.id}
                            isDragged={draggedId === obj.id}
                            onDragStart={handleDragStart}
                        />
                    ))}
                </Suspense>
            </Canvas>
        </div>
    );
};
