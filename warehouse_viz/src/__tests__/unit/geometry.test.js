import { describe, it, expect } from 'vitest';
import { snapToGridPosition } from '../../utils/geometry';

describe('geometry utilities', () => {
  describe('snapToGridPosition', () => {
    it('should snap position to grid with size 1', () => {
      const position = [1.3, 0, 2.7];
      const gridSize = 1;
      const snapped = snapToGridPosition(position, gridSize);
      
      expect(snapped).toEqual([1, 0, 3]);
    });

    it('should snap position to grid with size 0.5', () => {
      const position = [1.3, 0, 2.7];
      const gridSize = 0.5;
      const snapped = snapToGridPosition(position, gridSize);
      
      expect(snapped).toEqual([1.5, 0, 2.5]);
    });

    it('should snap position to grid with size 2', () => {
      const position = [3.2, 0, 5.8];
      const gridSize = 2;
      const snapped = snapToGridPosition(position, gridSize);
      
      expect(snapped).toEqual([4, 0, 6]);
    });

    it('should not snap Y coordinate', () => {
      const position = [1.3, 5.7, 2.7];
      const gridSize = 1;
      const snapped = snapToGridPosition(position, gridSize);
      
      expect(snapped).toEqual([1, 5.7, 3]);
    });

    it('should handle negative coordinates', () => {
      const position = [-1.3, 0, -2.7];
      const gridSize = 1;
      const snapped = snapToGridPosition(position, gridSize);
      
      expect(snapped).toEqual([-1, 0, -3]);
    });

    it('should handle positions already on grid', () => {
      const position = [2, 0, 4];
      const gridSize = 1;
      const snapped = snapToGridPosition(position, gridSize);
      
      expect(snapped).toEqual([2, 0, 4]);
    });

    it('should snap to nearest grid intersection (0.5 rounds up)', () => {
      const position = [1.5, 0, 2.5];
      const gridSize = 1;
      const snapped = snapToGridPosition(position, gridSize);
      
      expect(snapped).toEqual([2, 0, 2]);
    });
  });
});
