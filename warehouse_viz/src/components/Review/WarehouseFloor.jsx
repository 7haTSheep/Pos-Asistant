import React from 'react';


export const WarehouseFloor = ({ onDragMove, onDragEnd, onClickEmpty }) => {
    // We can add grid lines here later
    const handlePointerMove = (e) => {
        // e.point is the intersection point in world coordinates
        if (onDragMove) onDragMove(e.point);
    };

    const handlePointerUp = (e) => {
        if (onDragEnd) onDragEnd();
    };

    const handleClick = (e) => {
        // Deselect when clicking empty floor space
        if (onClickEmpty) onClickEmpty();
    };

    return (
        <mesh
            rotation={[-Math.PI / 2, 0, 0]}
            position={[0, -0.01, 0]}
            receiveShadow
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onClick={handleClick}
        >
            <planeGeometry args={[50, 50]} />
            <meshStandardMaterial color="#333" roughness={0.8} metalness={0.2} />
            <gridHelper args={[50, 50, '#555', '#222']} rotation={[-Math.PI / 2, 0, 0]} />
        </mesh>
    );
};
