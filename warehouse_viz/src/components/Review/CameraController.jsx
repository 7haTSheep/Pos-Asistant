import React, { useRef, useEffect, useState } from 'react';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

export const CameraController = () => {
    const controlsRef = useRef();
    const [ctrlHeld, setCtrlHeld] = useState(false);

    useEffect(() => {
        const down = (e) => { if (e.key === 'Control') setCtrlHeld(true); };
        const up = (e) => { if (e.key === 'Control') setCtrlHeld(false); };
        window.addEventListener('keydown', down);
        window.addEventListener('keyup', up);
        return () => {
            window.removeEventListener('keydown', down);
            window.removeEventListener('keyup', up);
        };
    }, []);

    // Dynamically swap right-click between PAN and ROTATE based on Ctrl
    useEffect(() => {
        if (controlsRef.current) {
            controlsRef.current.mouseButtons = {
                LEFT: -1,
                MIDDLE: THREE.MOUSE.DOLLY,
                RIGHT: ctrlHeld ? THREE.MOUSE.ROTATE : THREE.MOUSE.PAN,
            };
        }
    }, [ctrlHeld]);

    return (
        <OrbitControls
            ref={controlsRef}
            makeDefault
            minPolarAngle={0}
            maxPolarAngle={Math.PI / 2.2}
            minDistance={5}
            maxDistance={30}
        />
    );
};

