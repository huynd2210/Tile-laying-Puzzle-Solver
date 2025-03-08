class CandidatePlacement:
    """
    Represents a candidate placement of a piece on the board.

    Attributes:
      - piece_id: a string key identifying the piece from the library.
      - orientation: a tuple of (i,j) offsets for this orientation.
      - position: a (base_i, base_j) position on the board where the piece is anchored.
      - cells: a tuple of board cells (i,j) that are covered; computed as:
           (base_i + offset_i, base_j + offset_j) for each offset in the orientation.
      - var_id: the unique SAT variable id corresponding to this candidate.
    """

    def __init__(self, piece_id, orientation, position, var_id):
        self.piece_id = piece_id
        self.orientation = orientation  # tuple of (i,j)
        self.position = position  # (base_i, base_j)
        self.var_id = var_id
        self.cells = self.compute_cells()

    def compute_cells(self):
        base_i, base_j = self.position
        return tuple((base_i + di, base_j + dj) for di, dj in self.orientation)

    def __str__(self):
        return (f"Candidate(piece={self.piece_id}, pos={self.position}, "
                f"orient={self.orientation}, covers={self.cells}, var_id={self.var_id})")