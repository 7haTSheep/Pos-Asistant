import React from 'react';
import { useStore } from '../../store/store';

export const WarehouseFloor = () => {
    // We can add grid lines here later
    return (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]} receiveShadow>
            <planeGeometry args={[50, 50]} />
            <meshStandardMaterial color="#333" roughness={0.8} metalness={0.2} />
            <gridHelper args={[50, 50, '#555', '#222']} rotation={[-Math.PI / 2, 0, 0]} />
        </mesh>
    );
};
