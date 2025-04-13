from backend.coordinate import Coordinate
from backend.utils import normalize


class Piece:
    """
    Represents a piece with a given footprint.

    The piece is initialized via a list of coordinates (provided as paired numbers).
    For example, to create a domino piece (covering 2 cells), you might call:
       Piece(0,0,0,1, color="red")

    The internal offsets are based on a canonical position (imagine the piece placed at (0,0)
    on an empty board).
    """

    def __init__(self, *args, color="white"):
        self.offsetValues = []
        self.color = color
        if len(args) % 2 != 0:
            raise Exception("Invalid number of arguments: coordinates must be paired")
        self.initPiece(args)

    def initPiece(self, args):
        is_i = True
        temp_i = None
        for element in args:
            if is_i:
                temp_i = element
                is_i = False
            else:
                is_i = True
                self.offsetValues.append(Coordinate(temp_i, element))

    def get_offsets(self):
        """
        Returns the offsets as a tuple of (i,j) pairs.
        """
        return tuple((coord.i, coord.j) for coord in self.offsetValues)

    def get_orientations(self):
        """
        Generate all distinct orientations of the piece.

        The routine applies rotations (0, 90, 180, 270 degrees) and reflection (flipping horizontally)
        to produce possible orientations. Each orientation is normalized so that the smallest coordinate
        is (0,0). Duplicate orientations are removed.

        Returns a list of orientations. Each orientation is a tuple of (i,j) offset pairs.
        """
        base = self.get_offsets()
        # Define transformation functions:
        # identity, rotate 90: (i,j) -> (-j, i), rotate 180: (i,j) -> (-i, -j),
        # rotate 270: (i,j) -> (j, -i)
        transforms = [
            lambda i, j: (i, j),
            lambda i, j: (-j, i),
            lambda i, j: (-i, -j),
            lambda i, j: (j, -i)
        ]
        # For each transform, also consider horizontal flip (mirroring j coordinate)
        orientations = set()
        orientation_list = []
        for t in transforms:
            transformed = tuple(t(i, j) for i, j in base)
            norm = normalize(transformed)
            if norm not in orientations:
                orientations.add(norm)
                orientation_list.append(norm)
            # Apply horizontal flip on top of the transformation.
            flipped = tuple((-u, v) for u, v in transformed)
            norm_flipped = normalize(flipped)
            if norm_flipped not in orientations:
                orientations.add(norm_flipped)
                orientation_list.append(norm_flipped)
        return orientation_list

    def __str__(self):
        return f"Piece(color={self.color}, offsets={self.get_offsets()})"