# Implementation Plan: Floor Plan Designer Remake

## Overview

This implementation plan transforms the existing warehouse_viz application into a professional floor plan designer tool. The approach follows an incremental development strategy, building core functionality first, then adding features layer by layer, with testing integrated throughout.

The implementation uses React 19.2.0, Three.js via React Three Fiber, Zustand for state management, and Tailwind CSS for styling. We'll set up property-based testing with fast-check alongside traditional unit tests using Vitest.

## Tasks

- [x] 1. Set up testing infrastructure and object type definitions
  - Install and configure fast-check for property-based testing
  - Create test arbitraries (generators) for objects, positions, and scene data
  - Define object type constants with categories, dimensions, and visual properties
  - Set up test directory structure (unit/ and properties/ folders)
  - _Requirements: 12.1-12.12, 2.7_

- [ ] 2. Implement core Zustand store with state management
  - [x] 2.1 Create store with objects array, selection, view mode, and grid settings
    - Define state interface with all required fields
    - Implement addObject action with UUID generation and default positioning
    - Implement updateObject action with immutable updates
    - Implement removeObject action
    - Implement setSelection, setViewMode, setGridSize, setSnapToGrid actions
    - _Requirements: 13.2, 13.3, 13.4, 13.5, 13.6_
  
  - [ ]* 2.2 Write property test for view mode preservation
    - **Property 1: View mode switching preserves object state**
    - **Validates: Requirements 1.5**
  
  - [ ]* 2.3 Write unit tests for store actions
    - Test adding objects creates correct structure
    - Test updating objects modifies only specified fields
    - Test removing objects by ID
    - Test selection state management
    - _Requirements: 13.5, 13.6_

- [ ] 3. Implement object library system with filtering
  - [x] 3.1 Create LibraryPanel component with search and category tabs
    - Implement search input with state management
    - Implement category tabs (All, Structure, Warehouse, Office)
    - Implement object list rendering with icons from Lucide
    - Add drag event handlers for drag-and-drop initiation
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6_
  
  - [ ]* 3.2 Write property test for category filtering
    - **Property 2: Category filtering shows only matching objects**
    - **Validates: Requirements 2.2**
  
  - [ ]* 3.3 Write property test for search filtering
    - **Property 3: Search filtering matches object names**
    - **Validates: Requirements 2.3**
  
  - [ ]* 3.4 Write property test for library object display information
    - **Property 4: Library objects contain required display information**
    - **Validates: Requirements 2.4**
  
  - [ ]* 3.5 Write unit tests for LibraryPanel interactions
    - Test clicking object adds it to scene
    - Test drag start sets correct data transfer
    - _Requirements: 2.5, 2.6_

- [ ] 4. Implement 3D scene rendering with basic objects
  - [ ] 4.1 Create Scene component with Canvas and drop handling
    - Set up React Three Fiber Canvas with camera and shadows
    - Implement drop event handlers with coordinate conversion
    - Implement grid snapping logic for drop positions
    - _Requirements: 3.3, 3.4, 3.5_
  
  - [ ] 4.2 Create FloorPlan component with lighting and grid
    - Add ambient and directional lights with shadows
    - Add grid helper and floor plane
    - Render objects from store state
    - _Requirements: 6.1, 16.1, 16.3_
  
  - [ ] 4.3 Create Object3D component with selection and dragging
    - Render box geometry with dimensions from object data
    - Apply colors based on object type
    - Implement pointer event handlers for selection
    - Implement drag-to-move functionality
    - Render selection outline when selected
    - _Requirements: 4.1, 4.3, 4.4, 16.1, 16.2, 16.4, 16.5_
  
  - [ ]* 4.4 Write property test for drop placement
    - **Property 6: Drop placement creates object at correct position**
    - **Validates: Requirements 3.3**
  
  - [ ]* 4.5 Write property test for grid snapping
    - **Property 7: Grid snapping aligns positions to grid intersections**
    - **Validates: Requirements 3.5, 6.3**
  
  - [ ]* 4.6 Write property test for automatic selection after placement
    - **Property 8: Placed objects are automatically selected**
    - **Validates: Requirements 3.6**
  
  - [ ]* 4.7 Write property test for object selection
    - **Property 9: Clicking objects selects them**
    - **Validates: Requirements 4.1**

- [ ] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement camera controls and view mode switching
  - [ ] 6.1 Create CameraController component
    - Implement 2D mode: orthographic top-down view with fixed rotation
    - Implement 3D mode: perspective view with orbit controls enabled
    - Add useEffect to switch camera configuration based on view mode
    - Disable rotation in 2D mode, enable in 3D mode
    - _Requirements: 1.1, 1.2, 1.4, 15.1, 15.2, 15.3, 15.4, 15.5, 15.6_
  
  - [ ] 6.2 Create Header component with view mode toggle
    - Add logo and title
    - Add 2D/3D toggle buttons with active state highlighting
    - Add action buttons (Load, Save, Export) with visual separators
    - Connect view mode buttons to store actions
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_
  
  - [ ]* 6.3 Write unit tests for view mode switching
    - Test 2D button sets orthographic camera
    - Test 3D button sets perspective camera with orbit controls
    - Test view mode persists in state
    - _Requirements: 1.1, 1.2, 1.6_

- [ ] 7. Implement properties panel with object editing
  - [ ] 7.1 Create PropertiesPanel component
    - Implement conditional rendering: scene settings when nothing selected, object properties when selected
    - Create Vector3Input component for position, rotation, dimensions
    - Display object type and ID as read-only fields
    - Add delete button that calls removeObject
    - Connect input changes to updateObject action
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_
  
  - [ ] 7.2 Create SceneSettings component
    - Add grid size input field
    - Add snap to grid toggle checkbox
    - Add floor dimensions inputs
    - Connect changes to store actions
    - _Requirements: 5.9, 6.5, 6.6_
  
  - [ ]* 7.3 Write property test for properties panel display
    - **Property 14: Properties panel displays selected object data**
    - **Validates: Requirements 5.2, 5.3**
  
  - [ ]* 7.4 Write property test for property changes
    - **Property 15: Property changes update objects immediately**
    - **Validates: Requirements 5.7**
  
  - [ ]* 7.5 Write property test for scene setting changes
    - **Property 16: Scene setting changes apply immediately**
    - **Validates: Requirements 5.9**
  
  - [ ]* 7.6 Write unit tests for properties panel
    - Test scene settings display when nothing selected
    - Test object properties display when object selected
    - Test delete button removes object
    - _Requirements: 5.1, 5.8_

- [ ] 8. Implement keyboard shortcuts for object manipulation
  - [ ] 8.1 Add keyboard event handlers to Scene or App component
    - Implement arrow key handlers for moving selected object
    - Implement Shift+arrow for fine-grained movement
    - Implement R key for 90-degree rotation
    - Implement Delete/Backspace for removing selected object
    - Implement Escape for deselecting
    - Add check to ignore shortcuts when input fields are focused
    - _Requirements: 4.5, 4.6, 4.7, 4.8, 4.9, 14.1, 14.2, 14.3, 14.4, 14.5, 14.8_
  
  - [ ] 8.2 Create ControlsHelp component with keyboard shortcuts overlay
    - Display help overlay with all keyboard shortcuts
    - Toggle visibility with ? key
    - Style as floating overlay with dark background
    - _Requirements: 14.6, 14.7, 15.7_
  
  - [ ]* 8.3 Write property test for arrow key movement
    - **Property 11: Arrow keys move selected objects**
    - **Validates: Requirements 4.5**
  
  - [ ]* 8.4 Write property test for rotation
    - **Property 12: R key rotates objects by 90 degrees**
    - **Validates: Requirements 4.7**
  
  - [ ]* 8.5 Write property test for deletion
    - **Property 13: Delete key removes selected objects**
    - **Validates: Requirements 4.8**
  
  - [ ]* 8.6 Write unit tests for keyboard shortcuts
    - Test Shift+arrow moves in smaller increments
    - Test Escape deselects all objects
    - Test shortcuts ignored when input focused
    - _Requirements: 4.6, 4.9, 14.8_

- [ ] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implement save and load functionality
  - [ ] 10.1 Create file operations utilities
    - Implement getSceneData function to serialize state to SceneData format
    - Implement loadScene function to deserialize and validate JSON
    - Add validation for required fields and data types
    - Implement error handling for invalid files
    - _Requirements: 7.1, 7.2, 7.3, 7.5, 7.6, 18.1_
  
  - [ ] 10.2 Add save and load actions to store
    - Implement clearScene action
    - Implement loadScene action that clears then applies loaded data
    - Add error state management for load failures
    - _Requirements: 7.7_
  
  - [ ] 10.3 Connect save/load buttons in Header
    - Implement Save button click handler to download JSON file
    - Implement Load button click handler to open file picker
    - Add file input element (hidden) for file selection
    - Display error messages on load failure
    - _Requirements: 7.4, 7.6_
  
  - [ ]* 10.4 Write property test for serialization completeness
    - **Property 17: Scene serialization is complete**
    - **Validates: Requirements 7.1, 7.2**
  
  - [ ]* 10.5 Write property test for save/load round-trip
    - **Property 18: Save and load round-trip preserves state**
    - **Validates: Requirements 7.5**
  
  - [ ]* 10.6 Write unit tests for file operations
    - Test invalid file shows error and maintains state
    - Test loading clears current scene first
    - Test save includes all required data
    - Test export JSON uses same format as save
    - _Requirements: 7.6, 7.7, 8.5_

- [ ] 11. Implement export functionality
  - [ ] 11.1 Create export utilities
    - Implement PNG export using canvas.toDataURL or similar
    - Implement JSON export (reuse save serialization)
    - Add file download trigger function
    - _Requirements: 8.2, 8.3, 8.4, 8.6_
  
  - [ ] 11.2 Add export UI to Header
    - Create export dropdown or modal with format options
    - Connect PNG export button to capture and download
    - Connect JSON export button to serialize and download
    - _Requirements: 8.1_
  
  - [ ]* 11.3 Write unit tests for export
    - Test PNG export triggers download
    - Test JSON export uses save format
    - Test export errors are handled gracefully
    - _Requirements: 8.2, 8.3, 8.5, 18.2_

- [ ] 12. Implement drag-to-move for selected objects
  - [ ] 12.1 Enhance Object3D drag handling
    - Track drag state (isDragging) in component
    - Update object position during pointer move when dragging
    - Apply grid snapping to drag positions if enabled
    - Render with reduced opacity while dragging
    - _Requirements: 4.4, 16.5_
  
  - [ ]* 12.2 Write property test for dragging movement
    - **Property 10: Dragging moves objects**
    - **Validates: Requirements 4.4**
  
  - [ ]* 12.3 Write unit tests for drag behavior
    - Test clicking empty space deselects
    - Test drag outside canvas doesn't create object
    - Test snap disabled allows free-form placement
    - _Requirements: 4.2, 3.4, 6.4_

- [ ] 13. Add visual polish and styling
  - [ ] 13.1 Apply Tailwind styling to all components
    - Use dark theme (gray-900, gray-800, gray-700)
    - Use blue accent colors for selections and interactive elements
    - Add hover effects to all interactive elements
    - Ensure consistent spacing and typography
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
  
  - [ ] 13.2 Implement responsive layout
    - Set LibraryPanel width to 256px (w-64)
    - Set PropertiesPanel width to 288px (w-72)
    - Set Canvas to flex-1 for remaining space
    - Add proper overflow handling and scrolling
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_
  
  - [ ] 13.3 Enhance 3D rendering quality
    - Configure shadow quality and resolution
    - Add smooth transitions for state changes
    - Optimize materials and lighting for realistic appearance
    - _Requirements: 11.6, 16.3, 16.6_

- [ ] 14. Performance optimization and error handling
  - [ ] 14.1 Add React.memo to expensive components
    - Memoize Object3D component
    - Memoize LibraryPanel object items
    - Add useMemo for filtered object lists
    - _Requirements: 17.2, 17.3_
  
  - [ ] 14.2 Implement comprehensive error handling
    - Add try-catch blocks around file operations
    - Add property validation for numeric inputs
    - Prevent NaN/Infinity values in object properties
    - Ensure selected ID always references existing object
    - Clear selection when selected object is deleted
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_
  
  - [ ]* 14.3 Write unit tests for error handling
    - Test invalid property values are rejected
    - Test selection cleared when object deleted
    - Test export failures maintain state
    - _Requirements: 18.2, 18.3_

- [ ] 15. Final integration and testing
  - [ ] 15.1 Add missing property-based tests
    - **Property 5: Adding objects from library creates them in scene**
    - **Validates: Requirements 2.5**
  
  - [ ]* 15.2 Write integration tests for complete workflows
    - Test complete workflow: add object → move → edit properties → save → load
    - Test drag-and-drop workflow from library to canvas
    - Test view mode switching with multiple objects
    - _Requirements: Multiple_
  
  - [ ] 15.3 Verify all object types are correctly defined
    - Test all 12 object types exist with correct default dimensions
    - Test all object types render with correct colors
    - Test all object types appear in correct categories
    - _Requirements: 12.1-12.12_

- [ ] 16. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test-related sub-tasks that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties with 100+ iterations
- Unit tests validate specific examples, edge cases, and error conditions
- The implementation builds incrementally: state → UI → 3D → interactions → persistence
- All property-based tests use fast-check with minimum 100 iterations
- Each property test includes a comment with the property number and text from the design document

