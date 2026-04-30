import logging

from backend.Solver import Solver

logger = logging.getLogger(__name__)


class BacktrackingSolver(Solver):
    """
    Stub backtracking solver for tiling puzzles.

    This is a placeholder implementation that demonstrates the Solver
    interface.  Replace the body of `solve` with a real backtracking
    algorithm when ready.
    """

    def solve(self, puzzle, max_solutions=1, **kwargs):
        """
        Stub implementation — always returns no solution.

        A real implementation would iterate over board cells, try placing
        candidates, recurse, and backtrack on conflicts.
        """
        logger.info("BacktrackingSolver.solve called (stub — returning no solutions)")

        # Normalise max_solutions
        unlimited = False
        if max_solutions is None:
            unlimited = True
        else:
            try:
                unlimited = int(max_solutions) <= 0
            except Exception:
                unlimited = False
        if not unlimited and max_solutions < 1:
            max_solutions = 1

        # TODO: implement real backtracking search here
        # Available data from puzzle:
        #   puzzle.board          — the Board object
        #   puzzle.piece_library  — dict of piece_id → Piece
        #   puzzle.candidates     — list of CandidatePlacement
        #   puzzle.cell_to_cands  — cell → [CandidatePlacement, ...]
        #   puzzle.piece_to_cands — piece_id → [CandidatePlacement, ...]
        #   puzzle.piece_usage_policy — AT_MOST_ONE or EXACTLY_ONE

        if not unlimited and max_solutions == 1:
            return None
        return []
