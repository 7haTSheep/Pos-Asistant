import React, { useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useStore } from '../../store/store';

import storageShelfSvg from '../../assets/sprites/storage_shelf.svg';
import palletRackSvg from '../../assets/sprites/pallet_rack.svg';
import binRackSvg from '../../assets/sprites/bin_rack.svg';
import cantileverRackSvg from '../../assets/sprites/cantilever_rack.svg';
import palletStackSvg from '../../assets/sprites/pallet_stack.svg';
import walkInRefrigeratorSvg from '../../assets/sprites/walk_in_refrigerator.svg';
import walkInFreezerSvg from '../../assets/sprites/walk_in_freezer.svg';
import coldRoomSvg from '../../assets/sprites/cold_room.svg';
import chillerUnitSvg from '../../assets/sprites/chiller_unit.svg';
import forkliftBaySvg from '../../assets/sprites/forklift_bay.svg';
import loadingDockSvg from '../../assets/sprites/loading_dock.svg';
import conveyorSvg from '../../assets/sprites/conveyor.svg';
import packingTableSvg from '../../assets/sprites/packing_table.svg';
import sortStationSvg from '../../assets/sprites/sort_station.svg';
import fireExtinguisherSvg from '../../assets/sprites/fire_extinguisher.svg';
import firstAidStationSvg from '../../assets/sprites/first_aid_station.svg';
import electricalPanelSvg from '../../assets/sprites/electrical_panel.svg';
import chargingStationSvg from '../../assets/sprites/charging_station.svg';
import defaultSvg from '../../assets/sprites/default.svg';

const ITEM_FOOTPRINT_SCALE = 0.32;
const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

const spritePathByType = {
    storage_shelf: storageShelfSvg,
    pallet_rack: palletRackSvg,
    bin_rack: binRackSvg,
    cantilever_rack: cantileverRackSvg,
    pallet_stack: palletStackSvg,
    walk_in_refrigerator: walkInRefrigeratorSvg,
    walk_in_freezer: walkInFreezerSvg,
    cold_room: coldRoomSvg,
    chiller_unit: chillerUnitSvg,
    forklift_bay: forkliftBaySvg,
    loading_dock: loadingDockSvg,
    conveyor: conveyorSvg,
    packing_table: packingTableSvg,
    sort_station: sortStationSvg,
    fire_extinguisher: fireExtinguisherSvg,
    first_aid_station: firstAidStationSvg,
    electrical_panel: electricalPanelSvg,
    charging_station: chargingStationSvg,
};

const textureCache = new Map();

const getTexture = (src) => {
    if (!src) return null;
    if (textureCache.has(src)) return textureCache.get(src);
    const texture = new THREE.TextureLoader().load(src);
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.minFilter = THREE.LinearFilter;
    texture.magFilter = THREE.LinearFilter;
    texture.wrapS = THREE.ClampToEdgeWrapping;
    texture.wrapT = THREE.ClampToEdgeWrapping;
    textureCache.set(src, texture);
    return texture;
};

export const Furniture = ({ id, position, rotation, size, dimensions, type, isSelected, isDragged, onDragStart }) => {
    const setSelection = useStore((state) => state.setSelection);
    const mesh = useRef();

    const handlePointerDown = (e) => {
        e.stopPropagation();
        if (onDragStart) {
            onDragStart(id, e.point, position);
        }
    };

    const handleClick = (e) => {
        e.stopPropagation();
        setSelection({ type: 'object', id });
    };

    // Support both 'size' and 'dimensions' for backwards compatibility
    const objectSize = size || dimensions || [1, 1, 1];
    const rawHeight = objectSize[1] || 1;
    const flatHeight = clamp(rawHeight * 0.22, 0.12, 1.35);
    const yLift = ((position?.[1] || 1) - 1) * 0.14;
    const rawWidth = (objectSize[0] || 1) * ITEM_FOOTPRINT_SCALE;
    const rawDepth = (objectSize[2] || 1) * ITEM_FOOTPRINT_SCALE;
    const renderWidth = clamp(rawWidth, 0.2, 3.2);
    const renderDepth = clamp(rawDepth, 0.2, 3.2);

    const spritePath = spritePathByType[type] || defaultSvg;
    const spriteTexture = useMemo(() => getTexture(spritePath), [spritePath]);

    return (
        <group position={[position[0], flatHeight / 2 + yLift, position[2]]} rotation={rotation}>
            <mesh
                ref={mesh}
                onClick={handleClick}
                onPointerDown={handlePointerDown}
                raycast={isDragged ? () => null : undefined}
            >
                <boxGeometry args={[renderWidth, flatHeight, renderDepth]} />
                <meshBasicMaterial color={isSelected ? '#2563eb' : '#64748b'} />
            </mesh>

            <mesh
                position={[0, flatHeight / 2 + 0.01, 0]}
                rotation={[-Math.PI / 2, 0, 0]}
                raycast={() => null}
            >
                <planeGeometry args={[renderWidth * 0.94, renderDepth * 0.94]} />
                <meshBasicMaterial map={spriteTexture} transparent />
            </mesh>
        </group>
    );
};
