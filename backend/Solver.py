from abc import ABC, abstractmethod


class Solver(ABC):
    """
    Abstract base class for tiling puzzle solvers.

    Subclasses must implement the `solve` method, which receives a
    `TilingPuzzle` (containing the board, piece library, candidates, and
    cell/piece mappings) and returns solutions.
    """

    @abstractmethod
    def solve(self, puzzle, max_solutions=1, **kwargs):
        """
        Solve the tiling puzzle.

        Parameters
        ----------
        puzzle : TilingPuzzle
            A fully-initialised puzzle instance (board + candidates already
            generated).
        max_solutions : int
            Maximum number of solutions to return.
            - 1  → return a single solution (list of CandidatePlacement) or None.
            - >1 → return a list of solutions.
            - <=0 or None → unlimited; return all solutions found.
        **kwargs :
            Solver-specific options (e.g. ``threads`` for SAT solvers).

        Returns
        -------
        list or None
            When *max_solutions* == 1: a single solution list, or ``None``.
            Otherwise: a list of solution lists (may be empty).
        """
        ...
