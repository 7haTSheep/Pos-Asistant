# Test Infrastructure

This directory contains the testing infrastructure for the Floor Plan Designer application.

## Structure

```
__tests__/
├── setup.js                    # Test setup and configuration
├── unit/                       # Unit tests for specific functionality
│   └── objectTypes.test.js     # Tests for object type definitions
└── properties/                 # Property-based tests
    ├── arbitraries.js          # Fast-check generators for test data
    └── arbitraries.test.js     # Tests validating the generators
```

## Testing Approach

This project uses a dual testing approach:

### Unit Tests
- Test specific examples and edge cases
- Validate integration between components
- Located in `unit/` directory
- Use Vitest and @testing-library/react

### Property-Based Tests
- Test universal properties across many random inputs
- Validate correctness properties from the design document
- Located in `properties/` directory
- Use fast-check library with minimum 100 iterations per property

## Running Tests

```bash
# Run all tests once
npm run test:run

# Run tests in watch mode
npm test

# Run tests with UI
npm run test:ui
```

## Arbitraries (Generators)

The `arbitraries.js` file contains fast-check generators for creating random valid test data:

- `objectTypeIdArbitrary()` - Valid object type IDs
- `categoryArbitrary()` - Valid categories (Structure, Warehouse, Office)
- `positionArbitrary()` - 3D positions within floor plan bounds
- `rotationArbitrary()` - 3D rotations in radians
- `dimensionsArbitrary()` - Valid positive dimensions
- `object3DDataArbitrary()` - Complete object data structures
- `objectArrayArbitrary()` - Arrays of objects
- `gridSizeArbitrary()` - Valid grid sizes
- `viewModeArbitrary()` - View modes (2D/3D)
- `sceneDataArbitrary()` - Complete scene data
- `snappedPositionArbitrary()` - Grid-aligned positions

## Writing New Tests

### Unit Test Example

```javascript
import { describe, it, expect } from 'vitest'
import { myFunction } from '../../utils/myModule.js'

describe('My Module', () => {
  it('should do something specific', () => {
    const result = myFunction('input')
    expect(result).toBe('expected output')
  })
})
```

### Property-Based Test Example

```javascript
import { describe, it, expect } from 'vitest'
import fc from 'fast-check'
import { myArbitrary } from './arbitraries.js'

describe('My Properties', () => {
  it('Property X: Description of property', () => {
    // Feature: floor-plan-designer-remake, Property X: Description
    fc.assert(
      fc.property(myArbitrary(), (input) => {
        // Test that property holds for all inputs
        const result = myFunction(input)
        expect(result).toSatisfySomeCondition()
        return true
      }),
      { numRuns: 100 }
    )
  })
})
```

## Test Configuration

Test configuration is in `vite.config.js`:

- Environment: happy-dom (lightweight DOM implementation)
- Globals: enabled (no need to import describe, it, expect)
- Setup file: `src/__tests__/setup.js`
