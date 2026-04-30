import logging

from backend.CandidatePlacement import CandidatePlacement
from backend.PieceUsagePolicy import PieceUsagePolicy
from backend.board import Board

logger = logging.getLogger(__name__)


class TilingPuzzle:
    """
    Represents an instance of a tiling puzzle.

    Given a board and a piece library (a dictionary mapping piece keys to Piece
    objects), this class:
      - Generates all candidate placements on the board (for all orientations).
      - Exposes mappings from board cells and piece IDs to their candidates.

    Solving is delegated to a separate Solver implementation (e.g. PySatSolver,
    BacktrackingSolver) via the Solver interface.
    """

    def __init__(self, board: Board, piece_library: dict,
                 piece_usage_policy: PieceUsagePolicy = PieceUsagePolicy.AT_MOST_ONE):
        self.board = board
        self.piece_library = piece_library  # e.g., {"a": Piece(...), "b": Piece(...), ...}
        self.piece_usage_policy = piece_usage_policy
        self.candidates = []  # List of CandidatePlacement objects.

        # Maps for solvers to consume:
        self.cell_to_cands = {}   # board cell -> list of CandidatePlacement
        self.piece_to_cands = {}  # piece key  -> list of CandidatePlacement

        self._generate_candidates()

    def _is_valid_placement(self, orient, base_i, base_j):
        """Check if placing the given orientation at (base_i, base_j) is valid."""
        for di, dj in orient:
            ci, cj = base_i + di, base_j + dj
            if (ci, cj) in self.board.obstacles or not (0 <= ci < self.board.height and 0 <= cj < self.board.width):
                return False
        return True

    def _add_candidate(self, piece_id, orient, base_i, base_j):
        """Create and register a candidate placement."""
        candidate = CandidatePlacement(piece_id, orient, (base_i, base_j))
        self.candidates.append(candidate)
        # Update board cell mapping.
        for cell in candidate.cells:
            self.cell_to_cands.setdefault(cell, []).append(candidate)
        # Update piece mapping.
        self.piece_to_cands[piece_id].append(candidate)

    def _generate_candidates_for_orientation(self, piece_id, orient):
        """Generate all valid candidate placements for a specific piece orientation."""
        if not orient:
            return

        max_i = max(i for i, j in orient)
        max_j = max(j for i, j in orient)

        # For each anchor position where the piece fits on the board...
        for base_i in range(self.board.height - max_i):
            for base_j in range(self.board.width - max_j):
                if self._is_valid_placement(orient, base_i, base_j):
                    self._add_candidate(piece_id, orient, base_i, base_j)

    def _generate_candidates(self):
        """
        For each piece in the library, generate all candidate placements on the board.
        """
        for piece_id, piece in self.piece_library.items():
            # For this piece, keep track of candidates.
            self.piece_to_cands.setdefault(piece_id, [])
            for orient in piece.get_orientations():
                self._generate_candidates_for_orientation(piece_id, orient)
