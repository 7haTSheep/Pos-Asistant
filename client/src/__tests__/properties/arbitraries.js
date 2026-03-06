/**
 * Fast-check arbitraries (generators) for property-based testing
 * These generators create random valid test data for objects, positions, and scene data
 */

import fc from 'fast-check'
import { OBJECT_TYPES } from '../../utils/objectTypes.js'

/**
 * Generate a valid object type ID
 */
export const objectTypeIdArbitrary = () => 
  fc.constantFrom(...OBJECT_TYPES.map(type => type.id))

/**
 * Generate a valid category name
 */
export const categoryArbitrary = () =>
  fc.constantFrom('Structure', 'Warehouse', 'Office')

/**
 * Generate a 3D position [x, y, z]
 * Constrained to reasonable floor plan bounds
 */
export const positionArbitrary = () =>
  fc.tuple(
    fc.float({ min: -25, max: 25, noNaN: true }), // x
    fc.float({ min: 0, max: 10, noNaN: true }),   // y (height)
    fc.float({ min: -25, max: 25, noNaN: true })  // z
  )

/**
 * Generate a 3D rotation [x, y, z] in radians
 */
export const rotationArbitrary = () =>
  fc.tuple(
    fc.float({ min: 0, max: Math.fround(Math.PI * 2), noNaN: true }),
    fc.float({ min: 0, max: Math.fround(Math.PI * 2), noNaN: true }),
    fc.float({ min: 0, max: Math.fround(Math.PI * 2), noNaN: true })
  )

/**
 * Generate valid dimensions [width, height, depth]
 * All dimensions must be positive
 */
export const dimensionsArbitrary = () =>
  fc.tuple(
    fc.float({ min: Math.fround(0.1), max: 10, noNaN: true }),
    fc.float({ min: Math.fround(0.1), max: 10, noNaN: true }),
    fc.float({ min: Math.fround(0.1), max: 10, noNaN: true })
  )

/**
 * Generate a valid UUID-like string
 */
export const uuidArbitrary = () =>
  fc.uuid()

/**
 * Generate a complete Object3DData structure
 */
export const object3DDataArbitrary = () =>
  fc.record({
    id: uuidArbitrary(),
    type: objectTypeIdArbitrary(),
    position: positionArbitrary(),
    rotation: rotationArbitrary(),
    dimensions: dimensionsArbitrary()
  })

/**
 * Generate an array of Object3DData
 * @param {number} minLength - Minimum array length
 * @param {number} maxLength - Maximum array length
 */
export const objectArrayArbitrary = (minLength = 0, maxLength = 20) =>
  fc.array(object3DDataArbitrary(), { minLength, maxLength })

/**
 * Generate grid size (positive number, typically 0.5 to 2)
 */
export const gridSizeArbitrary = () =>
  fc.float({ min: Math.fround(0.25), max: 5, noNaN: true })

/**
 * Generate view mode ('2D' or '3D')
 */
export const viewModeArbitrary = () =>
  fc.constantFrom('2D', '3D')

/**
 * Generate floor dimensions
 */
export const floorDimensionsArbitrary = () =>
  fc.record({
    width: fc.float({ min: 10, max: 100, noNaN: true }),
    depth: fc.float({ min: 10, max: 100, noNaN: true })
  })

/**
 * Generate scene settings
 */
export const sceneSettingsArbitrary = () =>
  fc.record({
    gridSize: gridSizeArbitrary(),
    snapToGrid: fc.boolean(),
    viewMode: viewModeArbitrary(),
    floorDimensions: floorDimensionsArbitrary()
  })

/**
 * Generate complete scene data
 */
export const sceneDataArbitrary = () =>
  fc.record({
    version: fc.constant('1.0'),
    objects: objectArrayArbitrary(0, 15),
    settings: sceneSettingsArbitrary()
  })

/**
 * Generate a position that is snapped to a grid
 * @param {number} gridSize - Grid size to snap to
 */
export const snappedPositionArbitrary = (gridSize) =>
  fc.tuple(
    fc.integer({ min: -10, max: 10 }).map(n => n * gridSize),
    fc.float({ min: 0, max: 10, noNaN: true }),
    fc.integer({ min: -10, max: 10 }).map(n => n * gridSize)
  )

/**
 * Generate a search query string
 */
export const searchQueryArbitrary = () =>
  fc.oneof(
    fc.constant(''),
    fc.stringOf(fc.constantFrom('a', 'e', 'i', 'o', 'u', 'r', 's', 't'), { minLength: 1, maxLength: 5 }),
    fc.constantFrom('wall', 'desk', 'shelf', 'door', 'table')
  )
