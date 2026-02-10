import React, { useRef } from 'react';
import { OrbitControls } from '@react-three/drei';

export const CameraController = () => {
    const controlsRef = useRef();

    return (
        <OrbitControls
            ref={controlsRef}
            makeDefault
            minPolarAngle={0}
            maxPolarAngle={Math.PI / 2.2} // Limit to not go below ground too much
            minDistance={5}
            maxDistance={30}
        />
    );
};
