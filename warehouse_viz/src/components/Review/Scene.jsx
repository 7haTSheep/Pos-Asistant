import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { CameraController } from './CameraController';
import { WarehouseFloor } from './WarehouseFloor';
import { Environment } from '@react-three/drei';

import { useStore } from '../../store/store';
import { Furniture } from '../Objects/Furniture';

export const Scene = () => {
    const objects = useStore((state) => state.objects);
    const selection = useStore((state) => state.selection);

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
                    <WarehouseFloor />
                    <CameraController />
                    <Environment preset="city" />

                    {objects.map((obj) => (
                        <Furniture
                            key={obj.id}
                            {...obj}
                            isSelected={selection?.type === 'object' && selection.id === obj.id}
                        />
                    ))}
                </Suspense>
            </Canvas>
        </div>
    );
};
