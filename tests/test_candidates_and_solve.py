import unittest
import sys
import os

# Add parent directory to system path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.board import Board
from backend.piece import Piece
from backend.CandidatePlacement import CandidatePlacement
from backend.TilingPuzzle import TilingPuzzle


class TestCandidatePlacement(unittest.TestCase):
    def test_compute_cells(self):
        # Orientation covers (0,0) and (0,1)
        orientation = ((0, 0), (0, 1))
        cand = CandidatePlacement('X', orientation, (2, 3), 1)
        # Should translate by base position
        self.assertEqual(cand.cells, ((2, 3), (2, 4)))


class TestSolveBasics(unittest.TestCase):
    def test_unsatisfiable_small_board(self):
        # 1x2 board with a single triomino cannot be solved
        board = Board(2, 1)
        pieces = {
            'T': Piece(0, 0, 0, 1, 0, 2),  # length-3 line
        }
        puzzle = TilingPuzzle(board, pieces)
        solution = puzzle.solve()
        self.assertIsNone(solution)

    def test_multiple_solutions_enumeration(self):
        # 1x2 board with two single-cell pieces has two distinct assignments
        # Note: Board(height=1,width=2) → cells: (0,0),(0,1)
        board = Board(2, 1)
        pieces = {
            'A': Piece(0, 0),  # single cell
            'B': Piece(0, 0),  # another single cell (identical shape but distinct id)
        }
        puzzle = TilingPuzzle(board, pieces)
        solutions = puzzle.solve(max_solutions=2)
        # Should enumerate up to 2 solutions
        self.assertIsInstance(solutions, list)
        self.assertLessEqual(len(solutions), 2)
        self.assertGreater(len(solutions), 0)

    def test_unlimited_enumeration(self):
        # Same setup as above but request unlimited and ensure we get at least 2
        board = Board(2, 1)
        pieces = {
            'A': Piece(0, 0),
            'B': Piece(0, 0),
        }
        puzzle = TilingPuzzle(board, pieces)
        solutions = puzzle.solve(max_solutions=0)
        self.assertIsInstance(solutions, list)
        self.assertGreaterEqual(len(solutions), 2)

    def test_extra_piece_allowed_atmost(self):
        # 1x1 board with two single-cell pieces: at-most-one per piece means
        # we can still solve by selecting exactly one candidate overall and
        # not using the other piece
        board = Board(1, 1)
        pieces = {
            'A': Piece(0, 0),
            'B': Piece(0, 0),
        }
        puzzle = TilingPuzzle(board, pieces)
        solution = puzzle.solve()
        self.assertIsNotNone(solution)
        if solution:
            # Should cover exactly the single cell once
            covered = set()
            for cand in solution:
                for cell in cand.cells:
                    covered.add(cell)
            self.assertEqual(covered, {(0, 0)})

    def test_threads_argument_path(self):
        # Ensure code path with threads kwarg doesn't crash
        board = Board(1, 2)
        pieces = {
            'A': Piece(0, 0),
            'B': Piece(0, 0),
        }
        puzzle = TilingPuzzle(board, pieces)
        # Try with threads=2 (may fall back if solver doesn't support threads)
        sols = puzzle.solve(max_solutions=2, threads=2)
        self.assertIsInstance(sols, list)


if __name__ == '__main__':
    unittest.main()


