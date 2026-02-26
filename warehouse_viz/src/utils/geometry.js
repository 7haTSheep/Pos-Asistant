/**
 * Geometry and positioning utilities for the floor plan designer
 */

/**
 * Snap a position to the nearest grid intersection
 * @param {[number, number, number]} position - Position to snap [x, y, z]
 * @param {number} gridSize - Grid cell size in meters
 * @returns {[number, number, number]} Snapped position
 */
export const snapToGridPosition = (position, gridSize) => {
  const [x, y, z] = position;
  return [
    Math.round(x / gridSize) * gridSize,
    y, // Don't snap Y axis (height)
    Math.round(z / gridSize) * gridSize
  ];
};

/**
 * Convert screen coordinates to world position on the floor plane
 * @param {number} clientX - Mouse X position in pixels
 * @param {number} clientY - Mouse Y position in pixels
 * @param {DOMRect} rect - Canvas bounding rectangle
 * @param {THREE.Camera} camera - Three.js camera
 * @param {THREE.Scene} scene - Three.js scene
 * @returns {[number, number, number] | null} World position [x, y, z] or null if no intersection
 */
export const screenToWorldPosition = (clientX, clientY, rect, camera, scene, raycaster) => {
  // Calculate normalized device coordinates (-1 to +1)
  const x = ((clientX - rect.left) / rect.width) * 2 - 1;
  const y = -((clientY - rect.top) / rect.height) * 2 + 1;

  raycaster.setFromCamera({ x, y }, camera);

  // Find intersection with the floor
  const intersects = raycaster.intersectObjects(scene.children, true);
  const floorHit = intersects.find(hit => hit.object.userData.isFloor);

  if (floorHit) {
    const point = floorHit.point;
    return [point.x, 0, point.z];
  }

  return null;
};
