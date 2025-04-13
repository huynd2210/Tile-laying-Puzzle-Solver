import unittest
import sys
import os

# Add parent directory to system path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.board import Board
from backend.piece import Piece
from backend.TilingPuzzle import TilingPuzzle
from backend.pieceLibrary import test_piece_library


class TestBoardObstacles(unittest.TestCase):
    """Test cases for the Board class's obstacle functionality."""

    def setUp(self):
        """Set up a board for each test."""
        self.board = Board(4, 3)
        # Standard test obstacles in a diagonal pattern
        self.obstacles = [(0, 0), (1, 1), (2, 2)]

    def test_add_obstacles(self):
        """Test adding obstacles to the board."""
        self.board.addObstacles(self.obstacles)
        self.assertEqual(len(self.board.obstacles), 3)
        for obs in self.obstacles:
            self.assertIn(obs, self.board.obstacles)

    def test_get_obstacles(self):
        """Test getting the list of obstacles."""
        self.board.addObstacles(self.obstacles)
        stored_obstacles = self.board.getObstacles()
        self.assertEqual(len(stored_obstacles), 3)
        for obs in self.obstacles:
            self.assertIn(obs, stored_obstacles)

    def test_is_obstacle(self):
        """Test checking if a position is an obstacle."""
        self.board.addObstacles(self.obstacles)
        for i in range(self.board.height):
            for j in range(self.board.width):
                if (i, j) in self.obstacles:
                    self.assertTrue(self.board.isObstacle(i, j))
                else:
                    self.assertFalse(self.board.isObstacle(i, j))

    def test_remove_obstacle(self):
        """Test removing a specific obstacle."""
        self.board.addObstacles(self.obstacles)
        self.board.removeObstacle((0, 0))
        self.assertNotIn((0, 0), self.board.obstacles)
        self.assertEqual(len(self.board.obstacles), 2)

    def test_clear_obstacles(self):
        """Test clearing all obstacles."""
        self.board.addObstacles(self.obstacles)
        self.board.clearObstacles()
        self.assertEqual(len(self.board.obstacles), 0)

    def test_count_obstacles(self):
        """Test counting obstacles."""
        self.board.addObstacles(self.obstacles)
        self.assertEqual(self.board.count_obstacles(), 3)

    def test_cells_method_with_obstacles(self):
        """Test that cells() method correctly excludes obstacles."""
        self.board.addObstacles(self.obstacles)
        cells = self.board.cells()
        expected_cells = [(i, j) for i in range(self.board.height) 
                          for j in range(self.board.width) 
                          if (i, j) not in self.obstacles]
        
        # Check that cells() returns the right number of cells
        self.assertEqual(len(cells), self.board.width * self.board.height - len(self.obstacles))
        
        # Check that cells() returns all non-obstacle cells
        for cell in expected_cells:
            self.assertIn(cell, cells)
        
        # Check that cells() doesn't return any obstacle cells
        for obs in self.obstacles:
            self.assertNotIn(obs, cells)

    def test_in_bounds_with_obstacles(self):
        """Test that in_bounds() method correctly considers obstacles as out of bounds."""
        self.board.addObstacles(self.obstacles)
        
        # Test regular bounds
        self.assertFalse(self.board.in_bounds(-1, 0))
        self.assertFalse(self.board.in_bounds(0, -1))
        self.assertFalse(self.board.in_bounds(self.board.height, 0))
        self.assertFalse(self.board.in_bounds(0, self.board.width))
        
        # Test obstacles are considered out of bounds
        for obs in self.obstacles:
            self.assertFalse(self.board.in_bounds(*obs))
        
        # Test valid positions are in bounds
        for i in range(self.board.height):
            for j in range(self.board.width):
                if (i, j) not in self.obstacles:
                    self.assertTrue(self.board.in_bounds(i, j))

    def test_invalid_obstacle(self):
        """Test adding an invalid obstacle (out of bounds)."""
        with self.assertRaises(ValueError):
            self.board.addObstacles([(self.board.height, 0)])
        with self.assertRaises(ValueError):
            self.board.addObstacles([(0, self.board.width)])
        with self.assertRaises(ValueError):
            self.board.addObstacles([(-1, 0)])


class TestTilingPuzzleWithObstacles(unittest.TestCase):
    """Test cases for the TilingPuzzle class's handling of obstacles."""

    def setUp(self):
        """Set up a board with obstacles for each test."""
        self.board = Board(4, 3)
        self.obstacles = [(0, 0)]  # Simple obstacle at top-left
        self.board.addObstacles(self.obstacles)
        self.piece_lib = test_piece_library

    def test_candidate_generation_with_obstacles(self):
        """Test that candidate generation respects obstacles."""
        puzzle = TilingPuzzle(self.board, self.piece_lib)
        
        # Make sure candidates were generated
        self.assertGreater(len(puzzle.candidates), 0)
        
        # Check that no candidate covers an obstacle
        for candidate in puzzle.candidates:
            for cell in candidate.cells:
                self.assertNotIn(cell, self.obstacles, 
                               f"Candidate {candidate.piece_id} covers obstacle at {cell}")

    def test_solution_with_obstacles(self):
        """Test that solving respects obstacles."""
        puzzle = TilingPuzzle(self.board, self.piece_lib)
        solution = puzzle.solve()
        
        # Make sure a solution was found
        self.assertIsNotNone(solution, "Failed to find a solution with obstacles")
        
        # Check that the solution doesn't cover any obstacles
        covered_cells = set()
        for candidate in solution:
            for cell in candidate.cells:
                self.assertNotIn(cell, self.obstacles, 
                               f"Solution piece {candidate.piece_id} covers obstacle at {cell}")
                covered_cells.add(cell)
        
        # Check that all non-obstacle cells are covered
        expected_cells = {(i, j) for i in range(self.board.height) 
                         for j in range(self.board.width) 
                         if (i, j) not in self.obstacles}
        self.assertEqual(covered_cells, expected_cells, 
                       "Solution doesn't cover all non-obstacle cells")

    def test_multiple_obstacles(self):
        """Test with multiple obstacles in different patterns."""
        # Test with obstacles in a row
        board = Board(4, 3)
        row_obstacles = [(0, j) for j in range(4)]  # Entire top row
        board.addObstacles(row_obstacles)
        
        puzzle = TilingPuzzle(board, self.piece_lib)
        solution = puzzle.solve()
        
        if solution:
            # If a solution exists, verify it doesn't cover obstacles
            for candidate in solution:
                for cell in candidate.cells:
                    self.assertNotIn(cell, row_obstacles)
        
        # Test with obstacles in a column
        board = Board(4, 3)
        col_obstacles = [(i, 0) for i in range(3)]  # Entire left column
        board.addObstacles(col_obstacles)
        
        puzzle = TilingPuzzle(board, self.piece_lib)
        solution = puzzle.solve()
        
        if solution:
            # If a solution exists, verify it doesn't cover obstacles
            for candidate in solution:
                for cell in candidate.cells:
                    self.assertNotIn(cell, col_obstacles)

    def test_custom_piece_with_obstacles(self):
        """Test solving with a custom set of pieces and obstacles."""
        board = Board(3, 3)
        obstacles = [(1, 1)]  # Center cell is obstacle
        board.addObstacles(obstacles)
        
        # Create a custom piece library with simple pieces that can cover the board
        custom_lib = {
            "A": Piece(0, 0, 0, 1, color="red"),      # Vertical domino
            "B": Piece(0, 0, 1, 0, color="blue"),     # Horizontal domino
            "C": Piece(0, 0, color="green"),          # Single cell
            "D": Piece(0, 0, color="yellow"),         # Single cell
            "E": Piece(0, 0, color="magenta"),        # Single cell
            "F": Piece(0, 0, color="cyan"),           # Single cell
            "G": Piece(0, 0, color="white"),          # Single cell
            "H": Piece(0, 0, color="black"),          # Single cell
        }
        
        puzzle = TilingPuzzle(board, custom_lib)
        solution = puzzle.solve()
        
        # Check candidates respect obstacles
        for candidate in puzzle.candidates:
            for cell in candidate.cells:
                self.assertNotIn(cell, obstacles,
                               f"Candidate {candidate.piece_id} covers obstacle at {cell}")
        
        # If a solution exists, verify it respects obstacles
        if solution:
            # Check all pieces in the solution respect obstacles
            for candidate in solution:
                for cell in candidate.cells:
                    self.assertNotIn(cell, obstacles,
                                  f"Solution piece {candidate.piece_id} covers obstacle at {cell}")
                    
            # Optional: Verify solution covers all non-obstacle cells
            covered_cells = set()
            for candidate in solution:
                covered_cells.update(candidate.cells)
                
            expected_cells = {(i, j) for i in range(board.height) 
                            for j in range(board.width) 
                            if (i, j) not in obstacles}
            self.assertEqual(covered_cells, expected_cells, 
                          "Solution doesn't cover all non-obstacle cells")


if __name__ == "__main__":
    unittest.main() 