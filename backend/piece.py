from backend.utils import compute_orientations


class Piece:
    """
    Represents a piece with a given footprint.

    The piece is initialized via a list of (i, j) coordinate tuples.
    For example, to create a domino piece (covering 2 cells):
       Piece([(0, 0), (0, 1)], color="red")

    The internal offsets are based on a canonical position (imagine the piece
    placed at (0, 0) on an empty board).
    """

    def __init__(self, coordinates, color="white"):
        self.color = color
        self.offsetValues = [tuple(coord) for coord in coordinates]

    def get_offsets(self):
        """Returns the offsets as a tuple of (i, j) pairs."""
        return tuple(self.offsetValues)

    def get_orientations(self, allow_reflections=True, allow_rotations=True):
        """
        Generate all distinct orientations of the piece.

        Delegates to the shared ``compute_orientations`` utility so that the
        logic is not duplicated between ``Piece`` and ``JSONPieceAdapter``.
        """
        return compute_orientations(
            self.get_offsets(),
            allow_reflections=allow_reflections,
            allow_rotations=allow_rotations,
        )

    def __str__(self):
        return f"Piece(color={self.color}, offsets={self.get_offsets()})"