import { describe, it, expect, beforeEach } from 'vitest'
import { useStore } from '../../store/store'

describe('Floor Plan Designer Store', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    const store = useStore.getState()
    store.clearScene()
    store.setViewMode('2D')
    store.setGridSize(1)
    store.setSnapToGrid(true)
    store.setFloorDimensions({ width: 50, depth: 50 })
  })

  describe('addObject', () => {
    it('should add object with correct structure', () => {
      const store = useStore.getState()
      store.addObject('desk', [5, 0, 5])

      const objects = useStore.getState().objects
      expect(objects).toHaveLength(1)
      expect(objects[0]).toMatchObject({
        type: 'desk',
        position: [5, 0, 5],
        rotation: [0, 0, 0],
        dimensions: [1.5, 0.75, 0.8] // Default desk dimensions
      })
      expect(objects[0].id).toBeDefined()
      expect(typeof objects[0].id).toBe('string')
    })

    it('should use default position [0, 0, 0] when not provided', () => {
      const store = useStore.getState()
      store.addObject('chair')

      const objects = useStore.getState().objects
      expect(objects[0].position).toEqual([0, 0, 0])
    })

    it('should use default dimensions from object type', () => {
      const store = useStore.getState()
      store.addObject('wall')

      const objects = useStore.getState().objects
      expect(objects[0].dimensions).toEqual([1, 2, 0.2])
    })

    it('should generate unique IDs for each object', () => {
      const store = useStore.getState()
      store.addObject('desk')
      store.addObject('chair')
      store.addObject('table')

      const objects = useStore.getState().objects
      const ids = objects.map(obj => obj.id)
      const uniqueIds = new Set(ids)
      expect(uniqueIds.size).toBe(3)
    })

    it('should automatically select newly added object', () => {
      const store = useStore.getState()
      store.addObject('desk')

      const state = useStore.getState()
      expect(state.selectedId).toBe(state.objects[0].id)
    })
  })

  describe('updateObject', () => {
    it('should update only specified fields', () => {
      const store = useStore.getState()
      store.addObject('desk', [0, 0, 0])
      const objectId = useStore.getState().objects[0].id

      store.updateObject(objectId, { position: [10, 0, 10] })

      const updatedObject = useStore.getState().objects[0]
      expect(updatedObject.position).toEqual([10, 0, 10])
      expect(updatedObject.rotation).toEqual([0, 0, 0]) // Unchanged
      expect(updatedObject.dimensions).toEqual([1.5, 0.75, 0.8]) // Unchanged
    })

    it('should update multiple fields at once', () => {
      const store = useStore.getState()
      store.addObject('chair')
      const objectId = useStore.getState().objects[0].id

      store.updateObject(objectId, {
        position: [5, 0, 5],
        rotation: [0, Math.PI / 2, 0],
        dimensions: [1, 1, 1]
      })

      const updatedObject = useStore.getState().objects[0]
      expect(updatedObject.position).toEqual([5, 0, 5])
      expect(updatedObject.rotation).toEqual([0, Math.PI / 2, 0])
      expect(updatedObject.dimensions).toEqual([1, 1, 1])
    })

    it('should not modify other objects', () => {
      const store = useStore.getState()
      store.addObject('desk', [0, 0, 0])
      store.addObject('chair', [5, 0, 5])
      const firstId = useStore.getState().objects[0].id

      store.updateObject(firstId, { position: [10, 0, 10] })

      const objects = useStore.getState().objects
      expect(objects[0].position).toEqual([10, 0, 10])
      expect(objects[1].position).toEqual([5, 0, 5]) // Unchanged
    })

    it('should handle immutable updates correctly', () => {
      const store = useStore.getState()
      store.addObject('desk')
      const objectId = useStore.getState().objects[0].id
      const originalObject = useStore.getState().objects[0]

      store.updateObject(objectId, { position: [1, 0, 1] })

      const updatedObject = useStore.getState().objects[0]
      expect(updatedObject).not.toBe(originalObject) // New object reference
      expect(updatedObject.id).toBe(originalObject.id) // Same ID
    })
  })

  describe('removeObject', () => {
    it('should remove object by ID', () => {
      const store = useStore.getState()
      store.addObject('desk')
      store.addObject('chair')
      const firstId = useStore.getState().objects[0].id

      store.removeObject(firstId)

      const objects = useStore.getState().objects
      expect(objects).toHaveLength(1)
      expect(objects[0].type).toBe('chair')
    })

    it('should clear selection if removed object was selected', () => {
      const store = useStore.getState()
      store.addObject('desk')
      const objectId = useStore.getState().objects[0].id

      store.removeObject(objectId)

      expect(useStore.getState().selectedId).toBeNull()
    })

    it('should not clear selection if different object was removed', () => {
      const store = useStore.getState()
      store.addObject('desk')
      store.addObject('chair')
      const firstId = useStore.getState().objects[0].id
      const secondId = useStore.getState().objects[1].id

      store.setSelection(firstId)
      store.removeObject(secondId)

      expect(useStore.getState().selectedId).toBe(firstId)
    })

    it('should handle removing non-existent object gracefully', () => {
      const store = useStore.getState()
      store.addObject('desk')

      expect(() => store.removeObject('non-existent-id')).not.toThrow()
      expect(useStore.getState().objects).toHaveLength(1)
    })
  })

  describe('setSelection', () => {
    it('should set selected object ID', () => {
      const store = useStore.getState()
      store.addObject('desk')
      const objectId = useStore.getState().objects[0].id

      store.setSelection(objectId)

      expect(useStore.getState().selectedId).toBe(objectId)
    })

    it('should allow deselecting by passing null', () => {
      const store = useStore.getState()
      store.addObject('desk')
      const objectId = useStore.getState().objects[0].id
      store.setSelection(objectId)

      store.setSelection(null)

      expect(useStore.getState().selectedId).toBeNull()
    })

    it('should allow selecting different objects', () => {
      const store = useStore.getState()
      store.addObject('desk')
      store.addObject('chair')
      const firstId = useStore.getState().objects[0].id
      const secondId = useStore.getState().objects[1].id

      store.setSelection(firstId)
      expect(useStore.getState().selectedId).toBe(firstId)

      store.setSelection(secondId)
      expect(useStore.getState().selectedId).toBe(secondId)
    })
  })

  describe('setViewMode', () => {
    it('should set view mode to 2D', () => {
      const store = useStore.getState()
      store.setViewMode('3D')
      store.setViewMode('2D')

      expect(useStore.getState().viewMode).toBe('2D')
    })

    it('should set view mode to 3D', () => {
      const store = useStore.getState()
      store.setViewMode('3D')

      expect(useStore.getState().viewMode).toBe('3D')
    })
  })

  describe('setGridSize', () => {
    it('should set grid size', () => {
      const store = useStore.getState()
      store.setGridSize(2)

      expect(useStore.getState().gridSize).toBe(2)
    })

    it('should allow decimal grid sizes', () => {
      const store = useStore.getState()
      store.setGridSize(0.5)

      expect(useStore.getState().gridSize).toBe(0.5)
    })
  })

  describe('setSnapToGrid', () => {
    it('should enable snap to grid', () => {
      const store = useStore.getState()
      store.setSnapToGrid(false)
      store.setSnapToGrid(true)

      expect(useStore.getState().snapToGrid).toBe(true)
    })

    it('should disable snap to grid', () => {
      const store = useStore.getState()
      store.setSnapToGrid(false)

      expect(useStore.getState().snapToGrid).toBe(false)
    })
  })

  describe('setFloorDimensions', () => {
    it('should set floor dimensions', () => {
      const store = useStore.getState()
      store.setFloorDimensions({ width: 100, depth: 80 })

      expect(useStore.getState().floorDimensions).toEqual({ width: 100, depth: 80 })
    })
  })

  describe('getSceneData', () => {
    it('should return complete scene data', () => {
      const store = useStore.getState()
      store.addObject('desk', [5, 0, 5])
      store.setViewMode('3D')
      store.setGridSize(2)
      store.setSnapToGrid(false)

      const sceneData = store.getSceneData()

      expect(sceneData.version).toBe('1.0')
      expect(sceneData.objects).toHaveLength(1)
      expect(sceneData.settings).toEqual({
        gridSize: 2,
        snapToGrid: false,
        viewMode: '3D',
        floorDimensions: { width: 50, depth: 50 }
      })
    })

    it('should include all object properties', () => {
      const store = useStore.getState()
      store.addObject('chair', [10, 0, 10])

      const sceneData = store.getSceneData()
      const object = sceneData.objects[0]

      expect(object).toHaveProperty('id')
      expect(object).toHaveProperty('type')
      expect(object).toHaveProperty('position')
      expect(object).toHaveProperty('rotation')
      expect(object).toHaveProperty('dimensions')
    })
  })

  describe('loadScene', () => {
    it('should load scene data correctly', () => {
      const sceneData = {
        version: '1.0',
        objects: [
          {
            id: 'test-id-1',
            type: 'desk',
            position: [5, 0, 5],
            rotation: [0, Math.PI / 2, 0],
            dimensions: [1.5, 0.75, 0.8]
          }
        ],
        settings: {
          gridSize: 2,
          snapToGrid: false,
          viewMode: '3D',
          floorDimensions: { width: 100, depth: 80 }
        }
      }

      const store = useStore.getState()
      store.loadScene(sceneData)

      const state = useStore.getState()
      expect(state.objects).toEqual(sceneData.objects)
      expect(state.gridSize).toBe(2)
      expect(state.snapToGrid).toBe(false)
      expect(state.viewMode).toBe('3D')
      expect(state.floorDimensions).toEqual({ width: 100, depth: 80 })
    })

    it('should clear selection when loading scene', () => {
      const store = useStore.getState()
      store.addObject('desk')
      store.setSelection(useStore.getState().objects[0].id)

      store.loadScene({
        version: '1.0',
        objects: [],
        settings: {
          gridSize: 1,
          snapToGrid: true,
          viewMode: '2D',
          floorDimensions: { width: 50, depth: 50 }
        }
      })

      expect(useStore.getState().selectedId).toBeNull()
    })

    it('should use default values for missing settings', () => {
      const store = useStore.getState()
      store.loadScene({
        version: '1.0',
        objects: [],
        settings: {}
      })

      const state = useStore.getState()
      expect(state.gridSize).toBe(1)
      expect(state.snapToGrid).toBe(true)
      expect(state.viewMode).toBe('2D')
      expect(state.floorDimensions).toEqual({ width: 50, depth: 50 })
    })
  })

  describe('clearScene', () => {
    it('should remove all objects', () => {
      const store = useStore.getState()
      store.addObject('desk')
      store.addObject('chair')
      store.addObject('table')

      store.clearScene()

      expect(useStore.getState().objects).toHaveLength(0)
    })

    it('should clear selection', () => {
      const store = useStore.getState()
      store.addObject('desk')
      store.setSelection(useStore.getState().objects[0].id)

      store.clearScene()

      expect(useStore.getState().selectedId).toBeNull()
    })

    it('should not affect other settings', () => {
      const store = useStore.getState()
      store.setViewMode('3D')
      store.setGridSize(2)
      store.setSnapToGrid(false)

      store.clearScene()

      const state = useStore.getState()
      expect(state.viewMode).toBe('3D')
      expect(state.gridSize).toBe(2)
      expect(state.snapToGrid).toBe(false)
    })
  })
})
