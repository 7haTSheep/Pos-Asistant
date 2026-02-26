# Design Document: Floor Plan Designer Remake

## Overview

This design transforms the existing warehouse_viz application into a professional floor plan designer tool. The application provides a CAD-like interface for creating, editing, and exporting floor plans with both 2D blueprint and 3D visualization modes.

The system is built using React for UI components, Three.js (via React Three Fiber) for 3D rendering, Zustand for state management, and Tailwind CSS for styling. The architecture follows a component-based design with clear separation between UI, 3D rendering, and state management layers.

## Architecture

### Technology Stack

- **Frontend Framework**: React 19.2.0
- **3D Rendering**: Three.js 0.182.0 via @react-three/fiber 9.5.0
- **3D Utilities**: @react-three/drei 10.7.7 (for camera controls, helpers)
- **State Management**: Zustand 5.0.11
- **Styling**: Tailwind CSS 4.1.18
- **Icons**: Lucide React 0.563.0
- **Build Tool**: Vite 7.3.1
- **Unique IDs**: uuid 13.0.0

### Application Structure

```
warehouse_viz/
├── src/
│   ├── components/
│   │   ├── UI/
│   │   │   ├── Header.jsx           # Top navigation bar
│   │   │   ├── LibraryPanel.jsx     # Left sidebar with object library
│   │   │   ├── PropertiesPanel.jsx  # Right sidebar with properties
│   │   │   └── ControlsHelp.jsx     # Keyboard shortcuts overlay
│   │   └── Review/
│   │       ├── Scene.jsx            # Main 3D canvas wrapper
│   │       ├── FloorPlan.jsx        # 3D scene content
│   │       ├── Object3D.jsx         # Individual 3D object renderer
│   │       └── CameraController.jsx # View mode camera management
│   ├── store/
│   │   └── useStore.js              # Zustand state management
│   ├── utils/
│   │   ├── objectTypes.js           # Object type definitions
│   │   ├── fileOperations.js        # Save/load/export utilities
│   │   └── geometry.js              # 3D geometry helpers
│   └── App.jsx                      # Root component
```

### Component Hierarchy

```
App
├── Header
│   ├── Logo/Title
│   ├── View Mode Toggles (2D/3D)
│   └── Action Buttons (Load/Save/Export)
├── LibraryPanel
│   ├── Search Input
│   ├── Category Tabs
│   └── Object List (draggable items)
├── Scene (Canvas)
│   ├── CameraController
│   ├── Lighting
│   ├── Grid
│   ├── FloorPlan
│   │   └── Object3D[] (for each object in state)
│   └── OrbitControls / Camera
└── PropertiesPanel
    ├── Scene Settings (when nothing selected)
    └── Object Properties (when object selected)
```

## Components and Interfaces

### State Management (Zustand Store)

```javascript
// store/useStore.js
interface StoreState {
  // Scene data
  objects: Object3DData[]
  selectedId: string | null
  viewMode: '2D' | '3D'
  gridSize: number
  snapToGrid: boolean
  floorDimensions: { width: number, depth: number }
  
  // Actions
  addObject: (type: string, position?: [number, number, number]) => void
  updateObject: (id: string, updates: Partial<Object3DData>) => void
  removeObject: (id: string) => void
  setSelection: (id: string | null) => void
  setViewMode: (mode: '2D' | '3D') => void
  setGridSize: (size: number) => void
  setSnapToGrid: (enabled: boolean) => void
  loadScene: (sceneData: SceneData) => void
  clearScene: () => void
  getSceneData: () => SceneData
}

interface Object3DData {
  id: string
  type: string
  position: [number, number, number]
  rotation: [number, number, number]
  dimensions: [number, number, number]
}

interface SceneData {
  objects: Object3DData[]
  settings: {
    gridSize: number
    snapToGrid: boolean
    viewMode: '2D' | '3D'
    floorDimensions: { width: number, depth: number }
  }
}
```

### Object Type Definitions

```javascript
// utils/objectTypes.js
interface ObjectType {
  id: string
  name: string
  category: 'Structure' | 'Warehouse' | 'Office'
  defaultDimensions: [number, number, number]
  color: string
  icon: string
}

const OBJECT_TYPES: ObjectType[] = [
  // Structure
  { id: 'wall', name: 'Wall', category: 'Structure', 
    defaultDimensions: [1, 2, 0.2], color: '#8B7355', icon: 'Square' },
  { id: 'door', name: 'Door', category: 'Structure', 
    defaultDimensions: [1, 2, 0.1], color: '#654321', icon: 'DoorOpen' },
  { id: 'window', name: 'Window', category: 'Structure', 
    defaultDimensions: [1, 1, 0.1], color: '#87CEEB', icon: 'Square' },
  
  // Warehouse
  { id: 'shelf', name: 'Shelf', category: 'Warehouse', 
    defaultDimensions: [3, 4, 1.5], color: '#CD853F', icon: 'Box' },
  { id: 'rack', name: 'Rack', category: 'Warehouse', 
    defaultDimensions: [2, 3, 1], color: '#D2691E', icon: 'Grid3x3' },
  { id: 'pallet', name: 'Pallet', category: 'Warehouse', 
    defaultDimensions: [1.2, 0.15, 1], color: '#8B4513', icon: 'Package' },
  { id: 'fridge', name: 'Fridge', category: 'Warehouse', 
    defaultDimensions: [2, 3, 1.5], color: '#E0E0E0', icon: 'Refrigerator' },
  { id: 'freezer', name: 'Freezer', category: 'Warehouse', 
    defaultDimensions: [2, 2, 1.5], color: '#B0C4DE', icon: 'Snowflake' },
  
  // Office
  { id: 'desk', name: 'Desk', category: 'Office', 
    defaultDimensions: [1.5, 0.75, 0.8], color: '#8B4513', icon: 'RectangleHorizontal' },
  { id: 'chair', name: 'Chair', category: 'Office', 
    defaultDimensions: [0.5, 1, 0.5], color: '#696969', icon: 'Armchair' },
  { id: 'table', name: 'Table', category: 'Office', 
    defaultDimensions: [2, 0.75, 1], color: '#A0522D', icon: 'Table' },
  { id: 'cabinet', name: 'Cabinet', category: 'Office', 
    defaultDimensions: [1, 2, 0.5], color: '#8B7355', icon: 'Archive' }
]
```

### UI Components

#### Header Component
```javascript
// components/UI/Header.jsx
function Header() {
  const { viewMode, setViewMode } = useStore()
  
  return (
    <header className="h-16 bg-gray-800 border-b border-gray-700 flex items-center px-4">
      <div className="flex items-center gap-3">
        <Logo />
        <h1>Floor Plan Designer</h1>
      </div>
      
      <div className="flex-1" />
      
      <div className="flex items-center gap-4">
        <ViewModeToggle mode={viewMode} onChange={setViewMode} />
        <div className="h-6 w-px bg-gray-600" />
        <ActionButtons />
      </div>
    </header>
  )
}
```

#### Library Panel Component
```javascript
// components/UI/LibraryPanel.jsx
function LibraryPanel() {
  const [searchQuery, setSearchQuery] = useState('')
  const [activeCategory, setActiveCategory] = useState('all')
  const addObject = useStore(state => state.addObject)
  
  const filteredObjects = useMemo(() => {
    return OBJECT_TYPES.filter(obj => {
      const matchesSearch = obj.name.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesCategory = activeCategory === 'all' || obj.category === activeCategory
      return matchesSearch && matchesCategory
    })
  }, [searchQuery, activeCategory])
  
  const handleDragStart = (e, objectType) => {
    e.dataTransfer.setData('objectType', objectType.id)
  }
  
  return (
    <aside className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
      <SearchInput value={searchQuery} onChange={setSearchQuery} />
      <CategoryTabs active={activeCategory} onChange={setActiveCategory} />
      <ObjectList objects={filteredObjects} onDragStart={handleDragStart} />
    </aside>
  )
}
```

#### Properties Panel Component
```javascript
// components/UI/PropertiesPanel.jsx
function PropertiesPanel() {
  const { objects, selectedId, updateObject, removeObject } = useStore()
  const selectedObject = objects.find(obj => obj.id === selectedId)
  
  if (!selectedObject) {
    return <SceneSettings />
  }
  
  return (
    <aside className="w-72 bg-gray-800 border-l border-gray-700 p-4">
      <h3>Object Properties</h3>
      <div className="space-y-4">
        <PropertyField label="Type" value={selectedObject.type} readOnly />
        <PropertyField label="ID" value={selectedObject.id} readOnly />
        
        <Vector3Input 
          label="Position" 
          value={selectedObject.position}
          onChange={(pos) => updateObject(selectedObject.id, { position: pos })}
        />
        
        <Vector3Input 
          label="Rotation" 
          value={selectedObject.rotation}
          onChange={(rot) => updateObject(selectedObject.id, { rotation: rot })}
        />
        
        <Vector3Input 
          label="Dimensions" 
          value={selectedObject.dimensions}
          onChange={(dim) => updateObject(selectedObject.id, { dimensions: dim })}
        />
        
        <button onClick={() => removeObject(selectedObject.id)}>
          Delete Object
        </button>
      </div>
    </aside>
  )
}
```

### 3D Scene Components

#### Scene Component
```javascript
// components/Review/Scene.jsx
function Scene() {
  const { viewMode, addObject, snapToGrid, gridSize } = useStore()
  
  const handleDrop = (e) => {
    e.preventDefault()
    const objectType = e.dataTransfer.getData('objectType')
    
    // Calculate 3D position from drop coordinates
    const rect = e.currentTarget.getBoundingClientRect()
    const x = ((e.clientX - rect.left) / rect.width) * 2 - 1
    const y = -((e.clientY - rect.top) / rect.height) * 2 + 1
    
    // Convert to world coordinates (simplified)
    let position = [x * 10, 0, y * 10]
    
    if (snapToGrid) {
      position = snapToGridPosition(position, gridSize)
    }
    
    addObject(objectType, position)
  }
  
  return (
    <div 
      className="w-full h-full"
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
    >
      <Canvas shadows camera={{ position: [10, 10, 10], fov: 50 }}>
        <CameraController mode={viewMode} />
        <FloorPlan />
      </Canvas>
    </div>
  )
}
```

#### FloorPlan Component
```javascript
// components/Review/FloorPlan.jsx
function FloorPlan() {
  const { objects, selectedId, setSelection, gridSize, viewMode } = useStore()
  
  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 5]} intensity={1} castShadow />
      
      {/* Grid */}
      <gridHelper 
        args={[50, 50, '#444444', '#222222']} 
        position={[0, 0, 0]}
      />
      
      {/* Floor */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[50, 50]} />
        <meshStandardMaterial color="#1a1a1a" />
      </mesh>
      
      {/* Objects */}
      {objects.map(obj => (
        <Object3D
          key={obj.id}
          data={obj}
          isSelected={obj.id === selectedId}
          onSelect={() => setSelection(obj.id)}
        />
      ))}
    </>
  )
}
```

#### Object3D Component
```javascript
// components/Review/Object3D.jsx
function Object3D({ data, isSelected, onSelect }) {
  const meshRef = useRef()
  const { updateObject } = useStore()
  const [isDragging, setIsDragging] = useState(false)
  
  const objectType = OBJECT_TYPES.find(t => t.id === data.type)
  
  const handlePointerDown = (e) => {
    e.stopPropagation()
    onSelect()
    setIsDragging(true)
  }
  
  const handlePointerMove = (e) => {
    if (isDragging) {
      // Update position based on pointer movement
      const newPosition = [e.point.x, data.position[1], e.point.z]
      updateObject(data.id, { position: newPosition })
    }
  }
  
  const handlePointerUp = () => {
    setIsDragging(false)
  }
  
  return (
    <mesh
      ref={meshRef}
      position={data.position}
      rotation={data.rotation}
      castShadow
      receiveShadow
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
    >
      <boxGeometry args={data.dimensions} />
      <meshStandardMaterial 
        color={objectType?.color || '#888888'}
        opacity={isDragging ? 0.7 : 1}
        transparent={isDragging}
      />
      
      {isSelected && (
        <lineSegments>
          <edgesGeometry attach="geometry" args={[new BoxGeometry(...data.dimensions)]} />
          <lineBasicMaterial attach="material" color="#3b82f6" linewidth={2} />
        </lineSegments>
      )}
    </mesh>
  )
}
```

#### Camera Controller Component
```javascript
// components/Review/CameraController.jsx
function CameraController({ mode }) {
  const { camera, gl } = useThree()
  const controlsRef = useRef()
  
  useEffect(() => {
    if (mode === '2D') {
      // Orthographic top-down view
      camera.position.set(0, 20, 0)
      camera.lookAt(0, 0, 0)
      camera.up.set(0, 0, -1)
      
      if (controlsRef.current) {
        controlsRef.current.enableRotate = false
      }
    } else {
      // 3D perspective view
      camera.position.set(10, 10, 10)
      camera.lookAt(0, 0, 0)
      camera.up.set(0, 1, 0)
      
      if (controlsRef.current) {
        controlsRef.current.enableRotate = true
      }
    }
  }, [mode, camera])
  
  return <OrbitControls ref={controlsRef} args={[camera, gl.domElement]} />
}
```

## Data Models

### Object3DData
Represents a single object in the floor plan.

```javascript
{
  id: string,              // Unique identifier (UUID)
  type: string,            // Object type ID (e.g., 'wall', 'desk')
  position: [x, y, z],     // World position in meters
  rotation: [x, y, z],     // Euler angles in radians
  dimensions: [w, h, d]    // Width, height, depth in meters
}
```

### SceneData
Complete serializable scene state for save/load.

```javascript
{
  version: '1.0',
  objects: Object3DData[],
  settings: {
    gridSize: number,
    snapToGrid: boolean,
    viewMode: '2D' | '3D',
    floorDimensions: {
      width: number,
      depth: number
    }
  }
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Before defining the correctness properties, let me analyze each acceptance criterion for testability:



### Property 1: View mode switching preserves object state
*For any* scene with objects, switching between 2D and 3D view modes should preserve all object positions, rotations, and dimensions without modification.
**Validates: Requirements 1.5**

### Property 2: Category filtering shows only matching objects
*For any* category selection, all displayed objects in the library panel should belong to that category.
**Validates: Requirements 2.2**

### Property 3: Search filtering matches object names
*For any* search query, all displayed objects should have names that contain the search query (case-insensitive).
**Validates: Requirements 2.3**

### Property 4: Library objects contain required display information
*For any* object type in the library, its display representation should include an icon, name, and category.
**Validates: Requirements 2.4**

### Property 5: Adding objects from library creates them in scene
*For any* object type in the library, clicking or adding it should create a new object in the scene with the correct type and default dimensions.
**Validates: Requirements 2.5**

### Property 6: Drop placement creates object at correct position
*For any* valid drop location on the canvas, dropping an object should create it at that position (with grid snapping applied if enabled).
**Validates: Requirements 3.3**

### Property 7: Grid snapping aligns positions to grid intersections
*For any* object position when snap is enabled, the position coordinates should be multiples of the grid size.
**Validates: Requirements 3.5, 6.3**

### Property 8: Placed objects are automatically selected
*For any* newly placed object, it should become the selected object immediately after placement.
**Validates: Requirements 3.6**

### Property 9: Clicking objects selects them
*For any* object in the scene, clicking it should set it as the selected object.
**Validates: Requirements 4.1**

### Property 10: Dragging moves objects
*For any* selected object, dragging it should update its position to follow the drag movement.
**Validates: Requirements 4.4**

### Property 11: Arrow keys move selected objects
*For any* selected object and any arrow key direction, pressing the arrow key should move the object in the corresponding direction by a fixed increment.
**Validates: Requirements 4.5**

### Property 12: R key rotates objects by 90 degrees
*For any* selected object, pressing the R key should increase its Y-axis rotation by π/2 radians (90 degrees).
**Validates: Requirements 4.7**

### Property 13: Delete key removes selected objects
*For any* selected object, pressing Delete or Backspace should remove that object from the scene.
**Validates: Requirements 4.8**

### Property 14: Properties panel displays selected object data
*For any* selected object, the properties panel should display all of its properties (type, id, position, rotation, dimensions).
**Validates: Requirements 5.2, 5.3**

### Property 15: Property changes update objects immediately
*For any* selected object and any property field change, updating the property should immediately update the object in the scene.
**Validates: Requirements 5.7**

### Property 16: Scene setting changes apply immediately
*For any* scene setting change (grid size, snap toggle), the change should be immediately reflected in the scene behavior.
**Validates: Requirements 5.9**

### Property 17: Scene serialization is complete
*For any* scene state, serializing it to JSON should include all objects with their complete data (id, type, position, rotation, dimensions) and all scene settings.
**Validates: Requirements 7.1, 7.2**

### Property 18: Save and load round-trip preserves state
*For any* valid scene state, saving it to JSON and then loading it back should produce an equivalent scene with the same objects and settings.
**Validates: Requirements 7.5**

## Error Handling

### Invalid File Loading
- When loading a file, validate JSON structure before applying
- Check for required fields: `objects` array, `settings` object
- Validate each object has required fields: `id`, `type`, `position`, `rotation`, `dimensions`
- If validation fails, display error message and maintain current scene state
- Log detailed error information to console for debugging

### Property Validation
- Position, rotation, and dimension inputs should accept numeric values only
- Reject non-numeric inputs and display validation feedback
- Clamp values to reasonable ranges (e.g., dimensions > 0)
- Prevent NaN or Infinity values from being applied

### Export Failures
- Wrap export operations in try-catch blocks
- If PNG export fails, display error message and maintain current state
- If JSON export fails, display error message with details
- Log export errors to console

### Drag and Drop Errors
- Validate object type exists before creating object
- Handle cases where drop coordinates are invalid
- Prevent duplicate object creation on rapid clicks

### State Consistency
- Ensure selected object ID always references an existing object
- Clear selection if selected object is deleted
- Validate object IDs are unique when adding objects

## Testing Strategy

### Dual Testing Approach

This feature will use both unit tests and property-based tests for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs

Unit tests focus on specific scenarios and integration points, while property tests validate that correctness properties hold across many randomly generated inputs. Together, they provide comprehensive coverage.

### Property-Based Testing

We will use **fast-check** (JavaScript property-based testing library) to implement the correctness properties defined above. Each property test will:

- Run a minimum of 100 iterations with randomly generated inputs
- Reference its corresponding design document property in a comment
- Use the tag format: `Feature: floor-plan-designer-remake, Property {number}: {property_text}`

Example property test structure:

```javascript
import fc from 'fast-check'
import { describe, it, expect } from 'vitest'

describe('Floor Plan Designer Properties', () => {
  it('Property 1: View mode switching preserves object state', () => {
    // Feature: floor-plan-designer-remake, Property 1: View mode switching preserves object state
    fc.assert(
      fc.property(
        fc.array(objectArbitrary()),
        (objects) => {
          const store = createStore()
          objects.forEach(obj => store.addObject(obj.type, obj.position))
          
          const beforeSwitch = store.getState().objects
          store.setViewMode('3D')
          store.setViewMode('2D')
          const afterSwitch = store.getState().objects
          
          expect(afterSwitch).toEqual(beforeSwitch)
        }
      ),
      { numRuns: 100 }
    )
  })
})
```

### Unit Testing

Unit tests will cover:

- Specific UI interactions (button clicks, keyboard shortcuts)
- Edge cases (empty scenes, invalid inputs, boundary values)
- Error conditions (invalid file formats, missing data)
- Integration between components (drag-and-drop, selection updates)

Example unit test structure:

```javascript
import { describe, it, expect } from 'vitest'
import { render, fireEvent } from '@testing-library/react'

describe('Object Selection', () => {
  it('should deselect all objects when clicking empty space', () => {
    const store = createStore()
    store.addObject('desk', [0, 0, 0])
    store.setSelection(store.getState().objects[0].id)
    
    const { getByTestId } = render(<Scene />)
    fireEvent.click(getByTestId('canvas-background'))
    
    expect(store.getState().selectedId).toBeNull()
  })
})
```

### Test Organization

```
warehouse_viz/
├── src/
│   ├── __tests__/
│   │   ├── unit/
│   │   │   ├── store.test.js
│   │   │   ├── objectTypes.test.js
│   │   │   ├── fileOperations.test.js
│   │   │   └── components/
│   │   │       ├── Header.test.jsx
│   │   │       ├── LibraryPanel.test.jsx
│   │   │       └── PropertiesPanel.test.jsx
│   │   └── properties/
│   │       ├── viewMode.properties.test.js
│   │       ├── objectManipulation.properties.test.js
│   │       ├── serialization.properties.test.js
│   │       └── arbitraries.js  # Generators for property tests
```

### Testing Tools

- **Vitest**: Test runner and assertion library
- **@testing-library/react**: React component testing utilities
- **@testing-library/user-event**: User interaction simulation
- **fast-check**: Property-based testing library
- **@react-three/test-renderer**: Three.js component testing (if needed)

### Coverage Goals

- Minimum 80% code coverage for core logic
- All 18 correctness properties implemented as property tests
- All error handling paths covered by unit tests
- All keyboard shortcuts covered by unit tests
- Critical user flows covered by integration tests

## Implementation Notes

### State Management Patterns

The Zustand store should follow these patterns:

1. **Immutable Updates**: Always create new objects/arrays when updating state
2. **Computed Values**: Derive values like "selected object" from state rather than storing separately
3. **Action Composition**: Complex operations should compose simpler actions
4. **Persistence**: Use Zustand middleware for localStorage persistence if needed

### Performance Considerations

1. **Memoization**: Use React.memo for expensive components (Object3D, LibraryPanel items)
2. **Debouncing**: Debounce property input changes to avoid excessive updates
3. **Lazy Loading**: Lazy load 3D geometries and textures
4. **Instance Rendering**: Consider instanced rendering for many identical objects
5. **Frustum Culling**: Let Three.js handle frustum culling automatically

### Accessibility

1. **Keyboard Navigation**: All functionality accessible via keyboard
2. **Focus Management**: Proper focus indicators and tab order
3. **ARIA Labels**: Add aria-labels to interactive elements
4. **Screen Reader Support**: Provide text alternatives for visual information

### Browser Compatibility

- Target modern browsers (Chrome, Firefox, Safari, Edge)
- Minimum versions: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- WebGL 2.0 required for Three.js rendering
- ES2020+ JavaScript features used

### File Format Versioning

The scene JSON format should include a version field for future compatibility:

```javascript
{
  version: '1.0',
  objects: [...],
  settings: {...}
}
```

Future versions can implement migration logic to upgrade old formats.

