import React, { useRef } from 'react';
import { useStore } from '../../store/store';
import { Html } from '@react-three/drei';

export const Furniture = ({ id, position, rotation, size, type, isSelected }) => {
    const setSelection = useStore((state) => state.setSelection);
    const mesh = useRef();

    const handleClick = (e) => {
        e.stopPropagation();
        setSelection({ type: 'object', id });
    };

    const color = isSelected ? '#3b82f6' : (type === 'fridge' ? '#e5e7eb' : '#d97706');

    return (
        <group position={position} rotation={rotation}>
            <mesh ref={mesh} onClick={handleClick} castShadow receiveShadow>
                <boxGeometry args={size} />
                <meshStandardMaterial color={color} />
            </mesh>

            {/* Label */}
            <Html position={[0, size[1] / 2 + 0.5, 0]} center distanceFactor={10}>
                <div className="bg-black/50 text-white px-2 py-1 rounded text-xs whitespace-nowrap">
                    {type}
                </div>
            </Html>
        </group>
    );
};
