/**
 * Unit tests for object type definitions
 * Validates: Requirements 12.1-12.12, 2.7
 */

import { describe, it, expect } from 'vitest'
import { OBJECT_TYPES, getObjectType, getObjectTypesByCategory, getCategories } from '../../utils/objectTypes.js'

describe('Object Types', () => {
  describe('OBJECT_TYPES constant', () => {
    it('should contain exactly 12 object types', () => {
      expect(OBJECT_TYPES).toHaveLength(12)
    })

    it('should have all required fields for each object type', () => {
      OBJECT_TYPES.forEach(type => {
        expect(type).toHaveProperty('id')
        expect(type).toHaveProperty('name')
        expect(type).toHaveProperty('category')
        expect(type).toHaveProperty('defaultDimensions')
        expect(type).toHaveProperty('color')
        expect(type).toHaveProperty('icon')
      })
    })

    it('should have unique IDs for all object types', () => {
      const ids = OBJECT_TYPES.map(type => type.id)
      const uniqueIds = new Set(ids)
      expect(uniqueIds.size).toBe(OBJECT_TYPES.length)
    })

    it('should have valid dimensions (arrays of 3 positive numbers)', () => {
      OBJECT_TYPES.forEach(type => {
        expect(Array.isArray(type.defaultDimensions)).toBe(true)
        expect(type.defaultDimensions).toHaveLength(3)
        type.defaultDimensions.forEach(dim => {
          expect(typeof dim).toBe('number')
          expect(dim).toBeGreaterThan(0)
        })
      })
    })
  })

  describe('Structure category objects', () => {
    it('should have wall with correct dimensions [1, 2, 0.2]', () => {
      const wall = getObjectType('wall')
      expect(wall).toBeDefined()
      expect(wall.category).toBe('Structure')
      expect(wall.defaultDimensions).toEqual([1, 2, 0.2])
    })

    it('should have door with correct dimensions [1, 2, 0.1]', () => {
      const door = getObjectType('door')
      expect(door).toBeDefined()
      expect(door.category).toBe('Structure')
      expect(door.defaultDimensions).toEqual([1, 2, 0.1])
    })

    it('should have window with correct dimensions [1, 1, 0.1]', () => {
      const window = getObjectType('window')
      expect(window).toBeDefined()
      expect(window.category).toBe('Structure')
      expect(window.defaultDimensions).toEqual([1, 1, 0.1])
    })
  })

  describe('Warehouse category objects', () => {
    it('should have shelf with correct dimensions [3, 4, 1.5]', () => {
      const shelf = getObjectType('shelf')
      expect(shelf).toBeDefined()
      expect(shelf.category).toBe('Warehouse')
      expect(shelf.defaultDimensions).toEqual([3, 4, 1.5])
    })

    it('should have rack with correct dimensions [2, 3, 1]', () => {
      const rack = getObjectType('rack')
      expect(rack).toBeDefined()
      expect(rack.category).toBe('Warehouse')
      expect(rack.defaultDimensions).toEqual([2, 3, 1])
    })

    it('should have pallet with correct dimensions [1.2, 0.15, 1]', () => {
      const pallet = getObjectType('pallet')
      expect(pallet).toBeDefined()
      expect(pallet.category).toBe('Warehouse')
      expect(pallet.defaultDimensions).toEqual([1.2, 0.15, 1])
    })

    it('should have fridge with correct dimensions [2, 3, 1.5]', () => {
      const fridge = getObjectType('fridge')
      expect(fridge).toBeDefined()
      expect(fridge.category).toBe('Warehouse')
      expect(fridge.defaultDimensions).toEqual([2, 3, 1.5])
    })

    it('should have freezer with correct dimensions [2, 2, 1.5]', () => {
      const freezer = getObjectType('freezer')
      expect(freezer).toBeDefined()
      expect(freezer.category).toBe('Warehouse')
      expect(freezer.defaultDimensions).toEqual([2, 2, 1.5])
    })
  })

  describe('Office category objects', () => {
    it('should have desk with correct dimensions [1.5, 0.75, 0.8]', () => {
      const desk = getObjectType('desk')
      expect(desk).toBeDefined()
      expect(desk.category).toBe('Office')
      expect(desk.defaultDimensions).toEqual([1.5, 0.75, 0.8])
    })

    it('should have chair with correct dimensions [0.5, 1, 0.5]', () => {
      const chair = getObjectType('chair')
      expect(chair).toBeDefined()
      expect(chair.category).toBe('Office')
      expect(chair.defaultDimensions).toEqual([0.5, 1, 0.5])
    })

    it('should have table with correct dimensions [2, 0.75, 1]', () => {
      const table = getObjectType('table')
      expect(table).toBeDefined()
      expect(table.category).toBe('Office')
      expect(table.defaultDimensions).toEqual([2, 0.75, 1])
    })

    it('should have cabinet with correct dimensions [1, 2, 0.5]', () => {
      const cabinet = getObjectType('cabinet')
      expect(cabinet).toBeDefined()
      expect(cabinet.category).toBe('Office')
      expect(cabinet.defaultDimensions).toEqual([1, 2, 0.5])
    })
  })

  describe('getObjectType', () => {
    it('should return object type by ID', () => {
      const desk = getObjectType('desk')
      expect(desk).toBeDefined()
      expect(desk.id).toBe('desk')
      expect(desk.name).toBe('Desk')
    })

    it('should return undefined for non-existent ID', () => {
      const result = getObjectType('nonexistent')
      expect(result).toBeUndefined()
    })
  })

  describe('getObjectTypesByCategory', () => {
    it('should return all Structure objects', () => {
      const structureObjects = getObjectTypesByCategory('Structure')
      expect(structureObjects).toHaveLength(3)
      expect(structureObjects.every(obj => obj.category === 'Structure')).toBe(true)
    })

    it('should return all Warehouse objects', () => {
      const warehouseObjects = getObjectTypesByCategory('Warehouse')
      expect(warehouseObjects).toHaveLength(5)
      expect(warehouseObjects.every(obj => obj.category === 'Warehouse')).toBe(true)
    })

    it('should return all Office objects', () => {
      const officeObjects = getObjectTypesByCategory('Office')
      expect(officeObjects).toHaveLength(4)
      expect(officeObjects.every(obj => obj.category === 'Office')).toBe(true)
    })

    it('should return empty array for non-existent category', () => {
      const result = getObjectTypesByCategory('NonExistent')
      expect(result).toEqual([])
    })
  })

  describe('getCategories', () => {
    it('should return all three categories', () => {
      const categories = getCategories()
      expect(categories).toHaveLength(3)
      expect(categories).toContain('Structure')
      expect(categories).toContain('Warehouse')
      expect(categories).toContain('Office')
    })
  })
})
