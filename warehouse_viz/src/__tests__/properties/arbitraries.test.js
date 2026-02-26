/**
 * Property-based tests for arbitraries (generators)
 * Validates that generators produce valid test data
 */

import { describe, it, expect } from 'vitest'
import fc from 'fast-check'
import {
  objectTypeIdArbitrary,
  categoryArbitrary,
  positionArbitrary,
  rotationArbitrary,
  dimensionsArbitrary,
  object3DDataArbitrary,
  objectArrayArbitrary,
  gridSizeArbitrary,
  viewModeArbitrary,
  sceneDataArbitrary,
  snappedPositionArbitrary
} from './arbitraries.js'
import { OBJECT_TYPES } from '../../utils/objectTypes.js'

describe('Arbitraries (Generators)', () => {
  it('objectTypeIdArbitrary generates valid object type IDs', () => {
    fc.assert(
      fc.property(objectTypeIdArbitrary(), (typeId) => {
        const validIds = OBJECT_TYPES.map(t => t.id)
        return validIds.includes(typeId)
      }),
      { numRuns: 100 }
    )
  })

  it('categoryArbitrary generates valid categories', () => {
    fc.assert(
      fc.property(categoryArbitrary(), (category) => {
        return ['Structure', 'Warehouse', 'Office'].includes(category)
      }),
      { numRuns: 100 }
    )
  })

  it('positionArbitrary generates valid 3D positions', () => {
    fc.assert(
      fc.property(positionArbitrary(), (position) => {
        expect(Array.isArray(position)).toBe(true)
        expect(position).toHaveLength(3)
        
        const [x, y, z] = position
        expect(typeof x).toBe('number')
        expect(typeof y).toBe('number')
        expect(typeof z).toBe('number')
        expect(isNaN(x)).toBe(false)
        expect(isNaN(y)).toBe(false)
        expect(isNaN(z)).toBe(false)
        
        // Check bounds
        expect(x).toBeGreaterThanOrEqual(-25)
        expect(x).toBeLessThanOrEqual(25)
        expect(y).toBeGreaterThanOrEqual(0)
        expect(y).toBeLessThanOrEqual(10)
        expect(z).toBeGreaterThanOrEqual(-25)
        expect(z).toBeLessThanOrEqual(25)
        
        return true
      }),
      { numRuns: 100 }
    )
  })

  it('rotationArbitrary generates valid rotations in radians', () => {
    fc.assert(
      fc.property(rotationArbitrary(), (rotation) => {
        expect(Array.isArray(rotation)).toBe(true)
        expect(rotation).toHaveLength(3)
        
        rotation.forEach(angle => {
          expect(typeof angle).toBe('number')
          expect(isNaN(angle)).toBe(false)
          expect(angle).toBeGreaterThanOrEqual(0)
          // Allow slight floating point imprecision
          expect(angle).toBeLessThanOrEqual(Math.PI * 2 + 0.001)
        })
        
        return true
      }),
      { numRuns: 100 }
    )
  })

  it('dimensionsArbitrary generates valid positive dimensions', () => {
    fc.assert(
      fc.property(dimensionsArbitrary(), (dimensions) => {
        expect(Array.isArray(dimensions)).toBe(true)
        expect(dimensions).toHaveLength(3)
        
        dimensions.forEach(dim => {
          expect(typeof dim).toBe('number')
          expect(isNaN(dim)).toBe(false)
          expect(dim).toBeGreaterThan(0)
        })
        
        return true
      }),
      { numRuns: 100 }
    )
  })

  it('object3DDataArbitrary generates complete object data', () => {
    fc.assert(
      fc.property(object3DDataArbitrary(), (obj) => {
        expect(obj).toHaveProperty('id')
        expect(obj).toHaveProperty('type')
        expect(obj).toHaveProperty('position')
        expect(obj).toHaveProperty('rotation')
        expect(obj).toHaveProperty('dimensions')
        
        expect(typeof obj.id).toBe('string')
        expect(typeof obj.type).toBe('string')
        expect(Array.isArray(obj.position)).toBe(true)
        expect(Array.isArray(obj.rotation)).toBe(true)
        expect(Array.isArray(obj.dimensions)).toBe(true)
        
        return true
      }),
      { numRuns: 100 }
    )
  })

  it('objectArrayArbitrary generates arrays of objects', () => {
    fc.assert(
      fc.property(objectArrayArbitrary(0, 10), (objects) => {
        expect(Array.isArray(objects)).toBe(true)
        expect(objects.length).toBeLessThanOrEqual(10)
        
        objects.forEach(obj => {
          expect(obj).toHaveProperty('id')
          expect(obj).toHaveProperty('type')
        })
        
        return true
      }),
      { numRuns: 100 }
    )
  })

  it('gridSizeArbitrary generates positive grid sizes', () => {
    fc.assert(
      fc.property(gridSizeArbitrary(), (gridSize) => {
        expect(typeof gridSize).toBe('number')
        expect(isNaN(gridSize)).toBe(false)
        expect(gridSize).toBeGreaterThan(0)
        return true
      }),
      { numRuns: 100 }
    )
  })

  it('viewModeArbitrary generates valid view modes', () => {
    fc.assert(
      fc.property(viewModeArbitrary(), (viewMode) => {
        return viewMode === '2D' || viewMode === '3D'
      }),
      { numRuns: 100 }
    )
  })

  it('sceneDataArbitrary generates complete scene data', () => {
    fc.assert(
      fc.property(sceneDataArbitrary(), (sceneData) => {
        expect(sceneData).toHaveProperty('version')
        expect(sceneData).toHaveProperty('objects')
        expect(sceneData).toHaveProperty('settings')
        
        expect(sceneData.version).toBe('1.0')
        expect(Array.isArray(sceneData.objects)).toBe(true)
        
        expect(sceneData.settings).toHaveProperty('gridSize')
        expect(sceneData.settings).toHaveProperty('snapToGrid')
        expect(sceneData.settings).toHaveProperty('viewMode')
        expect(sceneData.settings).toHaveProperty('floorDimensions')
        
        return true
      }),
      { numRuns: 100 }
    )
  })

  it('snappedPositionArbitrary generates grid-aligned positions', () => {
    const gridSize = 1.0
    
    fc.assert(
      fc.property(snappedPositionArbitrary(gridSize), (position) => {
        const [x, y, z] = position
        
        // X and Z should be multiples of gridSize
        expect(x % gridSize).toBeCloseTo(0, 5)
        expect(z % gridSize).toBeCloseTo(0, 5)
        
        // Y can be any valid height
        expect(y).toBeGreaterThanOrEqual(0)
        expect(y).toBeLessThanOrEqual(10)
        
        return true
      }),
      { numRuns: 100 }
    )
  })
})
