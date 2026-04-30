import logging

from pysat.card import CardEnc
from pysat.formula import CNF
from pysat.solvers import Solver as PySATSolverEngine

from backend.Solver import Solver
from backend.PieceUsagePolicy import PieceUsagePolicy

logger = logging.getLogger(__name__)


class PySatSolver(Solver):
    """
    SAT-based solver using the PySAT library.

    Translates a TilingPuzzle's candidates into a CNF formula with:
      (1) Board coverage constraints (each cell covered exactly once).
      (2) Piece usage constraints (at-most-one or exactly-one per piece).
    Then solves via configurable PySAT engines (glucose4, cadical, minisat22).
    """

    def solve(self, puzzle, max_solutions=1, **kwargs):
        solver_name = kwargs.get('solver_name', 'glucose4')
        threads = kwargs.get('threads', None)

        # ── normalise max_solutions ──────────────────────────────────────
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

        # ── build variable mapping ───────────────────────────────────────
        var_counter = 1
        cand_to_var = {}
        var_to_cand = {}
        cell_to_vars = {}
        piece_to_vars = {}

        for cand in puzzle.candidates:
            cand_to_var[id(cand)] = var_counter
            var_to_cand[var_counter] = cand
            for cell in cand.cells:
                cell_to_vars.setdefault(cell, []).append(var_counter)
            piece_to_vars.setdefault(cand.piece_id, []).append(var_counter)
            var_counter += 1

        # ── check coverage feasibility ───────────────────────────────────
        unsat_due_to_coverage = False
        for cell in puzzle.board.cells():
            if cell not in cell_to_vars:
                unsat_due_to_coverage = True
                logger.warning("No candidate covers cell %s", cell)

        if unsat_due_to_coverage:
            if max_solutions == 1 and not unlimited:
                return None
            return []

        # ── build CNF ────────────────────────────────────────────────────
        cnf = CNF()

        # (1) Board coverage: each cell exactly one candidate
        for cell in puzzle.board.cells():
            var_list = cell_to_vars.get(cell, [])
            if var_list:
                enc = CardEnc.equals(lits=var_list, bound=1, encoding=1,
                                     top_id=var_counter)
                cnf.extend(enc.clauses)
                var_counter = enc.nv + 1

        # (2) Piece usage
        for piece_id, var_list in piece_to_vars.items():
            if var_list:
                if puzzle.piece_usage_policy == PieceUsagePolicy.EXACTLY_ONE:
                    enc = CardEnc.equals(lits=var_list, bound=1, encoding=1,
                                         top_id=var_counter)
                else:  # AT_MOST_ONE (default)
                    enc = CardEnc.atmost(lits=var_list, bound=1, encoding=1,
                                         top_id=var_counter)
                cnf.extend(enc.clauses)
                var_counter = enc.nv + 1
            else:
                logger.warning("No candidate placement for piece %s", piece_id)

        # ── solve ────────────────────────────────────────────────────────
        solutions = []

        def enumerate_solutions(solver):
            nonlocal solutions
            while (unlimited or len(solutions) < max_solutions) and solver.solve():
                model = solver.get_model()
                selected = []
                selected_vars = []
                for v in model:
                    if v > 0 and v in var_to_cand:
                        selected.append(var_to_cand[v])
                        selected_vars.append(v)
                solutions.append(selected)
                if selected_vars:
                    solver.add_clause([-v for v in selected_vars])
                else:
                    break

        solver_kwargs = {'name': solver_name, 'bootstrap_with': cnf.clauses}
        if isinstance(threads, int) and threads > 1:
            solver_kwargs['threads'] = threads

        def run_solver(kwargs):
            try:
                with PySATSolverEngine(**kwargs) as s:
                    enumerate_solutions(s)
            except TypeError:
                # Fallback if the underlying solver doesn't support 'threads'
                kwargs.pop('threads', None)
                with PySATSolverEngine(**kwargs) as s:
                    enumerate_solutions(s)

        try:
            run_solver(solver_kwargs)
        except Exception as e:
            logger.warning("Solver %s failed: %s", solver_kwargs.get('name'), e)
            try:
                solver_kwargs['name'] = 'cadical'
                run_solver(solver_kwargs)
            except Exception as e2:
                logger.warning("Solver cadical failed: %s", e2)
                solver_kwargs['name'] = 'minisat22'
                run_solver(solver_kwargs)

        # ── return ───────────────────────────────────────────────────────
        if not unlimited and max_solutions == 1:
            return solutions[0] if solutions else None
        return solutions
