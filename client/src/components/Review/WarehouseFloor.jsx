import React from 'react';


export const WarehouseFloor = ({ floor, onDragMove, onDragEnd, onClickEmpty, onPointerDown }) => {
    // Provide default floor if none is passed
    const width = floor?.dimensions?.width || 50;
    const depth = floor?.dimensions?.depth || 50;
    const gridVisible = floor?.floorGrid?.visible ?? true;
    const cellSize = Math.max(0.5, floor?.floorGrid?.cellSize || 1);
    const gridSize = Math.max(width, depth);
    const divisions = Math.max(1, Math.round(gridSize / cellSize));

    const handlePointerMove = (e) => {
        if (onDragMove) onDragMove(e.point);
    };

    const handlePointerUp = () => {
        if (onDragEnd) onDragEnd();
    };

    const handlePointerDown = (e) => {
        if (onPointerDown) onPointerDown(e.point);
    };

    const handleClick = (e) => {
        if (onClickEmpty) onClickEmpty(e.point);
    };

    return (
        <group>
            <mesh
                rotation={[-Math.PI / 2, 0, 0]}
                position={[0, -0.01, 0]}
                onPointerMove={handlePointerMove}
                onPointerUp={handlePointerUp}
                onPointerDown={handlePointerDown}
                onClick={handleClick}
            >
                <planeGeometry args={[width, depth]} />
                <meshBasicMaterial color="#e7e2cc" />
            </mesh>

            {gridVisible && (
                <gridHelper
                    args={[gridSize, divisions, '#9ca3af', '#d1d5db']}
                    position={[0, 0.01, 0]}
                />
            )}
        </group>
    );
};
