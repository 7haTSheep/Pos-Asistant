/**
 * Object type definitions for the floor plan designer
 * Each object type includes category, default dimensions, color, and icon
 */

export const OBJECT_TYPES = [
  // Structure Category
  {
    id: 'wall',
    name: 'Wall',
    category: 'Structure',
    defaultDimensions: [1, 2, 0.2],
    color: '#8B7355',
    icon: 'Square'
  },
  {
    id: 'door',
    name: 'Door',
    category: 'Structure',
    defaultDimensions: [1, 2, 0.1],
    color: '#654321',
    icon: 'DoorOpen'
  },
  {
    id: 'window',
    name: 'Window',
    category: 'Structure',
    defaultDimensions: [1, 1, 0.1],
    color: '#87CEEB',
    icon: 'Square'
  },

  // Warehouse Category
  {
    id: 'shelf',
    name: 'Shelf',
    category: 'Warehouse',
    defaultDimensions: [3, 4, 1.5],
    color: '#CD853F',
    icon: 'Box'
  },
  {
    id: 'rack',
    name: 'Rack',
    category: 'Warehouse',
    defaultDimensions: [2, 3, 1],
    color: '#D2691E',
    icon: 'Grid3x3'
  },
  {
    id: 'pallet',
    name: 'Pallet',
    category: 'Warehouse',
    defaultDimensions: [1.2, 0.15, 1],
    color: '#8B4513',
    icon: 'Package'
  },
  {
    id: 'fridge',
    name: 'Fridge',
    category: 'Warehouse',
    defaultDimensions: [2, 3, 1.5],
    color: '#E0E0E0',
    icon: 'Refrigerator'
  },
  {
    id: 'freezer',
    name: 'Freezer',
    category: 'Warehouse',
    defaultDimensions: [2, 2, 1.5],
    color: '#B0C4DE',
    icon: 'Snowflake'
  },

  // Office Category
  {
    id: 'desk',
    name: 'Desk',
    category: 'Office',
    defaultDimensions: [1.5, 0.75, 0.8],
    color: '#8B4513',
    icon: 'RectangleHorizontal'
  },
  {
    id: 'chair',
    name: 'Chair',
    category: 'Office',
    defaultDimensions: [0.5, 1, 0.5],
    color: '#696969',
    icon: 'Armchair'
  },
  {
    id: 'table',
    name: 'Table',
    category: 'Office',
    defaultDimensions: [2, 0.75, 1],
    color: '#A0522D',
    icon: 'Table'
  },
  {
    id: 'cabinet',
    name: 'Cabinet',
    category: 'Office',
    defaultDimensions: [1, 2, 0.5],
    color: '#8B7355',
    icon: 'Archive'
  }
]

/**
 * Get object type by ID
 * @param {string} id - Object type ID
 * @returns {Object|undefined} Object type definition
 */
export function getObjectType(id) {
  return OBJECT_TYPES.find(type => type.id === id)
}

/**
 * Get all object types for a specific category
 * @param {string} category - Category name ('Structure', 'Warehouse', 'Office')
 * @returns {Array} Array of object types in the category
 */
export function getObjectTypesByCategory(category) {
  return OBJECT_TYPES.filter(type => type.category === category)
}

/**
 * Get all available categories
 * @returns {Array} Array of unique category names
 */
export function getCategories() {
  return [...new Set(OBJECT_TYPES.map(type => type.category))]
}
