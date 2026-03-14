from pysat.card import CardEnc
from pysat.formula import CNF
from pysat.solvers import Solver

from backend.CandidatePlacement import CandidatePlacement
from backend.board import Board


class TilingPuzzle:
    """
    Represents an instance of a tiling puzzle.

    Given a board and a piece library (a dictionary mapping piece keys to Piece objects),
    this class:
      - Generates all candidate placements on the board (for all orientations)
      - Creates a SAT CNF encoding with the constraints:
            (a) each board cell is covered exactly once, and
            (b) each piece is used exactly once.
      - Solves the instance using PySAT.

    The candidate placements are stored as CandidatePlacement objects.
    """

    def __init__(self, board: Board, piece_library: dict):
        self.board = board
        self.piece_library = piece_library  # e.g., {"a": Piece(...), "b": Piece(...), ...}
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

    def _generate_candidates(self):
        """
        For each piece in the library, generate all candidate placements on the board.
        For each distinct orientation, slide the piece over every board cell (anchor position)
        such that every cell of the piece lies in-bounds.
        """
        for piece_id, piece in self.piece_library.items():
            orientations = piece.get_orientations()
            # For this piece, keep track of candidate var_ids.
            self.piece_to_vars.setdefault(piece_id, [])
            for orient in orientations:
                # Determine the bounding box of the orientation.
                max_i = max(i for i, j in orient)
                max_j = max(j for i, j in orient)
                # For each anchor position where the piece fits on the board...
                for base_i in range(self.board.height - max_i):
                    for base_j in range(self.board.width - max_j):
                        valid_placement = True
                        for di, dj in orient:
                            ci, cj = base_i + di, base_j + dj
                            if (ci, cj) in self.board.obstacles or not (0 <= ci < self.board.height and 0 <= cj < self.board.width):
                                valid_placement = False
                                break
                        
                        # Only add the candidate if it's a valid placement
                        if valid_placement:
                            # Create the candidate placement
                            candidate = CandidatePlacement(piece_id, orient, (base_i, base_j), self.var_counter)
                            self.candidates.append(candidate)
                            # Update board cell mapping.
                            for cell in candidate.cells:
                                self.cell_to_vars.setdefault(cell, []).append(self.var_counter)
                            # Update piece mapping.
                            self.piece_to_vars[piece_id].append(self.var_counter)
                            self.var_counter += 1
                        # Otherwise skip to the next candidate

    def _generate_constraints(self):
        """
        Build the SAT constraints:
          (1) Each board cell must be covered by exactly one candidate.
          (2) Each piece must be placed exactly once.
        """
        # (1) Board cell coverage: Each cell exactly one candidate covers it.
        for cell in self.board.cells():
            var_list = self.cell_to_vars.get(cell, [])
            if var_list:
                enc = CardEnc.equals(lits=var_list, bound=1, encoding=1, top_id=self.var_counter)
                self.cnf.extend(enc.clauses)
                self.var_counter = enc.nv + 1
            else:
                # No candidate covers this cell → unsatisfiable instance.
                self.unsat_due_to_coverage = True
                print(f"Warning: No candidate covers cell {cell}")
        # (2) Each piece used exactly once.
        for piece_id, var_list in self.piece_to_vars.items():
            if var_list:
                # enc = CardEnc.equals(lits=var_list, bound=1, encoding=1, top_id=self.var_counter)
                enc = CardEnc.atmost(lits=var_list, bound=1, encoding=1, top_id=self.var_counter)
                self.cnf.extend(enc.clauses)
                self.var_counter = enc.nv + 1
            else:
                print(f"Warning: No candidate placement for piece {piece_id}")

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
        except Exception as e:
            try:
                solver_kwargs['name'] = 'cadical'
                run_solver(solver_kwargs)
            except Exception:
                solver_kwargs['name'] = 'minisat22'
                run_solver(solver_kwargs)

        if not unlimited and max_solutions == 1:
            return solutions[0] if solutions else None
        return solutions
