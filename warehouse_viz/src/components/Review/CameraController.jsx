import React, { useRef } from 'react';
import { OrbitControls } from '@react-three/drei';

export const CameraController = ({ enabled = true }) => {
    const controlsRef = useRef();

    return (
        <OrbitControls
            ref={controlsRef}
            makeDefault
            enabled={enabled}
            minPolarAngle={0}
            maxPolarAngle={Math.PI / 2.2}
            minDistance={5}
            maxDistance={30}
        />
    );
};

