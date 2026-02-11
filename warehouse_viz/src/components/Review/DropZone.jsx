import React, { useEffect } from 'react';
import { useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { useStore } from '../../store/store';

export const DropZone = () => {
    const { gl, camera, scene } = useThree();
    const addObject = useStore((state) => state.addObject);

    useEffect(() => {
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

            const raycaster = new THREE.Raycaster();
            raycaster.setFromCamera({ x, y }, camera);

            // Find intersection with the floor
            // We assume the floor is named 'warehouse-floor' or check distinct objects
            const intersects = raycaster.intersectObjects(scene.children, true);

            const floorHit = intersects.find(hit => hit.object.userData.isFloor);

            if (floorHit) {
                const point = floorHit.point;
                // Snap to grid or just place? Let's just place at height 0 + size/2
                // We need to know size to place on top. Default to 0 height for now (center of object)
                // Store handles default size.
                // Let's place it at y=0, but the object origin might be center.
                // Furniture component centers geometry?
                // BoxGeometry centers at 0,0,0. Furniture places group at position.
                // So y should be size.y / 2.
                // We'll let the user adjust or handle it in addObject defaults.
                addObject(type, [point.x, 0, point.z]);
            }
        };

        gl.domElement.addEventListener('dragover', handleDragOver);
        gl.domElement.addEventListener('drop', handleDrop);

        return () => {
            gl.domElement.removeEventListener('dragover', handleDragOver);
            gl.domElement.removeEventListener('drop', handleDrop);
        };
    }, [gl, camera, scene, addObject]);

    return null;
};
