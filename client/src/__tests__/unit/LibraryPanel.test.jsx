import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { LibraryPanel } from '../../components/UI/LibraryPanel'
import { useStore } from '../../store/store'
import { OBJECT_TYPES } from '../../utils/objectTypes'

describe('LibraryPanel Component', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    const store = useStore.getState()
    store.clearScene()
  })

  it('should render search input', () => {
    render(<LibraryPanel />)
    const searchInput = screen.getByPlaceholderText('Search objects...')
    expect(searchInput).toBeDefined()
  })

  it('should render all category tabs', () => {
    render(<LibraryPanel />)
    expect(screen.getByText('All')).toBeDefined()
    expect(screen.getByText('Structure')).toBeDefined()
    expect(screen.getByText('Warehouse')).toBeDefined()
    expect(screen.getByText('Office')).toBeDefined()
  })

  it('should display all objects when "All" category is active', () => {
    render(<LibraryPanel />)
    
    // Check that objects from all categories are displayed
    expect(screen.getByText('Wall')).toBeDefined()
    expect(screen.getByText('Shelf')).toBeDefined()
    expect(screen.getByText('Desk')).toBeDefined()
  })

  it('should filter objects by category when category tab is clicked', () => {
    render(<LibraryPanel />)
    
    // Click Structure category
    const structureTab = screen.getByText('Structure')
    fireEvent.click(structureTab)
    
    // Should show structure objects
    expect(screen.getByText('Wall')).toBeDefined()
    expect(screen.getByText('Door')).toBeDefined()
    
    // Should not show warehouse or office objects
    expect(screen.queryByText('Shelf')).toBeNull()
    expect(screen.queryByText('Desk')).toBeNull()
  })

  it('should filter objects by search query', () => {
    render(<LibraryPanel />)
    
    const searchInput = screen.getByPlaceholderText('Search objects...')
    fireEvent.change(searchInput, { target: { value: 'desk' } })
    
    // Should show only Desk
    expect(screen.getByText('Desk')).toBeDefined()
    
    // Should not show other objects
    expect(screen.queryByText('Wall')).toBeNull()
    expect(screen.queryByText('Shelf')).toBeNull()
  })

  it('should filter objects case-insensitively', () => {
    render(<LibraryPanel />)
    
    const searchInput = screen.getByPlaceholderText('Search objects...')
    fireEvent.change(searchInput, { target: { value: 'DESK' } })
    
    expect(screen.getByText('Desk')).toBeDefined()
  })

  it('should add object to scene when clicked', () => {
    render(<LibraryPanel />)
    
    const deskButton = screen.getByText('Desk')
    fireEvent.click(deskButton)
    
    const state = useStore.getState()
    expect(state.objects).toHaveLength(1)
    expect(state.objects[0].type).toBe('desk')
  })

  it('should make object draggable', () => {
    render(<LibraryPanel />)
    
    const deskButton = screen.getByText('Desk').closest('button')
    expect(deskButton.draggable).toBe(true)
  })

  it('should set correct data on drag start', () => {
    render(<LibraryPanel />)
    
    const deskButton = screen.getByText('Desk').closest('button')
    const dataTransfer = {
      setData: vi.fn()
    }
    
    fireEvent.dragStart(deskButton, { dataTransfer })
    
    expect(dataTransfer.setData).toHaveBeenCalledWith('objectType', 'desk')
  })

  it('should display all 12 object types', () => {
    render(<LibraryPanel />)
    
    // Verify all object types are present
    const objectNames = OBJECT_TYPES.map(obj => obj.name)
    objectNames.forEach(name => {
      expect(screen.getByText(name)).toBeDefined()
    })
  })

  it('should combine category and search filters', () => {
    render(<LibraryPanel />)
    
    // Select Warehouse category
    const warehouseTab = screen.getByText('Warehouse')
    fireEvent.click(warehouseTab)
    
    // Search for "shelf"
    const searchInput = screen.getByPlaceholderText('Search objects...')
    fireEvent.change(searchInput, { target: { value: 'shelf' } })
    
    // Should show only Shelf (warehouse + matches search)
    expect(screen.getByText('Shelf')).toBeDefined()
    
    // Should not show other warehouse items
    expect(screen.queryByText('Rack')).toBeNull()
    expect(screen.queryByText('Fridge')).toBeNull()
  })
})
