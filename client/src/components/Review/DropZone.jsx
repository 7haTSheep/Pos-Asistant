import React, { useEffect } from 'react';
import { useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { useStore } from '../../store/store';
import { snapToGridPosition } from '../../utils/geometry';

/**
 * DropZone component handles drag-and-drop of objects from the library onto the canvas.
 * It converts screen coordinates to world positions and applies grid snapping if enabled.
 * 
 * Requirements: 3.3, 3.4, 3.5
 */
export const DropZone = () => {
    const { gl, camera, scene } = useThree();
    const addObject = useStore((state) => state.addObject);
    const snapToGrid = useStore((state) => state.snapToGrid);
    const gridSize = useStore((state) => state.gridSize);

    useEffect(() => {
        const raycaster = new THREE.Raycaster();

        const handleDragOver = (e) => {
            e.preventDefault();
        };

        const handleDrop = (e) => {
            e.preventDefault();

            const type = e.dataTransfer.getData('type');
            if (!type) return;

            // Calculate mouse position in normalized device coordinates (-1 to +1)
            const rect = gl.domElement.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
            const y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

            raycaster.setFromCamera({ x, y }, camera);

            // Find intersection with the floor
            const intersects = raycaster.intersectObjects(scene.children, true);
            const floorHit = intersects.find(hit => hit.object.userData.isFloor);

            if (floorHit) {
                const point = floorHit.point;
                let position = [point.x, 0, point.z];

                // Apply grid snapping if enabled
                if (snapToGrid) {
                    position = snapToGridPosition(position, gridSize);
                }

                addObject(type, position);
            }
        };

        gl.domElement.addEventListener('dragover', handleDragOver);
        gl.domElement.addEventListener('drop', handleDrop);

        return () => {
            gl.domElement.removeEventListener('dragover', handleDragOver);
            gl.domElement.removeEventListener('drop', handleDrop);
        };
    }, [gl, camera, scene, addObject, snapToGrid, gridSize]);

    return null;
};
