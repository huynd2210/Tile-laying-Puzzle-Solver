import logging

from pysat.card import CardEnc
from pysat.formula import CNF
from pysat.solvers import Solver

from backend.CandidatePlacement import CandidatePlacement
from backend.PieceUsagePolicy import PieceUsagePolicy
from backend.board import Board

logger = logging.getLogger(__name__)


class TilingPuzzle:
    """
    Represents an instance of a tiling puzzle.

    Given a board and a piece library (a dictionary mapping piece keys to Piece
    objects), this class:
      - Generates all candidate placements on the board (for all orientations)
      - Creates a SAT CNF encoding with the constraints:
            (a) each board cell is covered exactly once, and
            (b) each piece is used according to the chosen *piece_usage_policy*
                (``AT_MOST_ONE`` by default, or ``EXACTLY_ONE``).
      - Solves the instance using PySAT.

    The candidate placements are stored as CandidatePlacement objects.
    """

    def __init__(self, board: Board, piece_library: dict,
                 piece_usage_policy: PieceUsagePolicy = PieceUsagePolicy.AT_MOST_ONE):
        self.board = board
        self.piece_library = piece_library  # e.g., {"a": Piece(...), "b": Piece(...), ...}
        self.piece_usage_policy = piece_usage_policy
        self.candidates = []  # List of CandidatePlacement objects.
        self.cnf = CNF()  # SAT formula.
        self.var_counter = 1  # Unique variable ids.
        # If any board cell cannot be covered by any candidate, the instance is unsatisfiable.
        self.unsat_due_to_coverage = False

        # Maps for constraints:
        self.cell_to_vars = {}  # board cell -> list of candidate var_ids.
        self.piece_to_vars = {}  # piece key -> list of candidate var_ids.

        self._generate_candidates()
        self._generate_constraints()

    def _is_valid_placement(self, orient, base_i, base_j):
        """Check if placing the given orientation at (base_i, base_j) is valid."""
        for di, dj in orient:
            ci, cj = base_i + di, base_j + dj
            if (ci, cj) in self.board.obstacles or not (0 <= ci < self.board.height and 0 <= cj < self.board.width):
                return False
        return True

    def _add_candidate(self, piece_id, orient, base_i, base_j):
        """Create and register a candidate placement."""
        candidate = CandidatePlacement(piece_id, orient, (base_i, base_j), self.var_counter)
        self.candidates.append(candidate)
        # Update board cell mapping.
        for cell in candidate.cells:
            self.cell_to_vars.setdefault(cell, []).append(self.var_counter)
        # Update piece mapping.
        self.piece_to_vars[piece_id].append(self.var_counter)
        self.var_counter += 1

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
            # For this piece, keep track of candidate var_ids.
            self.piece_to_vars.setdefault(piece_id, [])
            for orient in piece.get_orientations():
                self._generate_candidates_for_orientation(piece_id, orient)

    def _generate_board_coverage_constraints(self):
        """(1) Board cell coverage: Each cell exactly one candidate covers it."""
        for cell in self.board.cells():
            var_list = self.cell_to_vars.get(cell, [])
            if var_list:
                enc = CardEnc.equals(lits=var_list, bound=1, encoding=1, top_id=self.var_counter)
                self.cnf.extend(enc.clauses)
                self.var_counter = enc.nv + 1
            else:
                # No candidate covers this cell → unsatisfiable instance.
                self.unsat_due_to_coverage = True
                logger.warning("No candidate covers cell %s", cell)

    def _generate_piece_usage_constraints(self):
        """(2) Piece usage constraint."""
        for piece_id, var_list in self.piece_to_vars.items():
            if var_list:
                if self.piece_usage_policy == PieceUsagePolicy.EXACTLY_ONE:
                    enc = CardEnc.equals(lits=var_list, bound=1, encoding=1, top_id=self.var_counter)
                else:  # AT_MOST_ONE (default)
                    enc = CardEnc.atmost(lits=var_list, bound=1, encoding=1, top_id=self.var_counter)
                self.cnf.extend(enc.clauses)
                self.var_counter = enc.nv + 1
            else:
                logger.warning("No candidate placement for piece %s", piece_id)

    def _generate_constraints(self):
        """
        Build the SAT constraints:
          (1) Each board cell must be covered by exactly one candidate.
          (2) Each piece must be placed according to the piece usage policy.
        """
        self._generate_board_coverage_constraints()
        self._generate_piece_usage_constraints()

    def solve(self, solver_name='glucose4', max_solutions=1, threads=None):
        """
        Solve the SAT instance.

        - If max_solutions == 1 (default): returns a single solution as a list of CandidatePlacement
          objects, or None if unsatisfiable.
        - If max_solutions > 1: returns a list of solutions, where each solution is a list of
          CandidatePlacement objects. Returns [] if none found.
        """
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

        # If coverage constraints already imply UNSAT, short-circuit.
        if self.unsat_due_to_coverage:
            if max_solutions is None or (isinstance(max_solutions, int) and max_solutions != 1) or (not isinstance(max_solutions, int)):
                return []
            return None

        solutions = []

        solver_kwargs = {'name': solver_name, 'bootstrap_with': self.cnf.clauses}
        if isinstance(threads, int) and threads > 1:
            solver_kwargs['threads'] = threads

        def enumerate_solutions(solver):
            nonlocal solutions
            while (unlimited or len(solutions) < max_solutions) and solver.solve():
                model = solver.get_model()
                selected = []
                selected_vars = []
                for cand in self.candidates:
                    if cand.var_id in model:
                        selected.append(cand)
                        selected_vars.append(cand.var_id)
                solutions.append(selected)
                if selected_vars:
                    solver.add_clause([-v for v in selected_vars])
                else:
                    break

        def run_solver(kwargs):
            try:
                with Solver(**kwargs) as solver:
                    enumerate_solutions(solver)
            except TypeError:
                # Fallback if the underlying solver doesn't support 'threads'
                kwargs.pop('threads', None)
                with Solver(**kwargs) as solver:
                    enumerate_solutions(solver)

        try:
            run_solver(solver_kwargs)
        except Exception:
            try:
                solver_kwargs['name'] = 'cadical'
                run_solver(solver_kwargs)
            except Exception:
                solver_kwargs['name'] = 'minisat22'
                run_solver(solver_kwargs)

        if not unlimited and max_solutions == 1:
            return solutions[0] if solutions else None
        return solutions
