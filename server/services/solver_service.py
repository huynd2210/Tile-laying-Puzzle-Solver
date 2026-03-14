from backend.utils import normalize, compute_orientations


class JSONPieceAdapter:
    """
    Adapts a JSON piece dictionary to the same interface as ``Piece``,
    so both can be used interchangeably in the solver.
    """

    def __init__(self, piece_dict):
        self.name = piece_dict.get('name')
        self.color = piece_dict.get('color')
        self.cells = piece_dict.get('cells') or []
        self.allow_reflections = piece_dict.get('allow_reflections', True)
        self.allow_rotations = piece_dict.get('allow_rotations', True)

    def get_offsets(self):
        return tuple(tuple(coord) for coord in self.cells)

    def get_orientations(self, allow_reflections=None, allow_rotations=None):
        """Delegate to the shared ``compute_orientations`` utility."""
        return compute_orientations(
            self.get_offsets(),
            allow_reflections=self.allow_reflections if allow_reflections is None else allow_reflections,
            allow_rotations=self.allow_rotations if allow_rotations is None else allow_rotations,
        )


def _orientation_signature(orientation):
    """Create a canonical string signature from a normalized orientation."""
    coords = sorted(list(orientation))
    return ';'.join(f"{i}:{j}" for i, j in coords)


def _shape_signature(piece_obj):
    """Compute a canonical signature for a piece's shape across all orientations."""
    try:
        orientations = piece_obj.get_orientations()
        if not orientations:
            if hasattr(piece_obj, 'get_offsets'):
                base = piece_obj.get_offsets()
                base_norm = normalize(tuple(base))
                orientations = [base_norm] if base_norm else []
        sigs = [_orientation_signature(o) for o in orientations]
        return min(sigs) if sigs else ''
    except Exception:
        return ''


def group_equivalent_pieces(piece_lib: dict):
    """
    Group pieces that have the same shape (identical set of orientations).

    Returns:
        (grouped_lib, id_map) where grouped_lib contains one representative
        per shape, and id_map maps every original piece_id to its canonical id.
    """
    grouped = {}
    seen = {}
    id_map = {}
    for pid, pobj in piece_lib.items():
        sig = _shape_signature(pobj)
        if sig in seen:
            id_map[pid] = seen[sig]
            continue
        seen[sig] = pid
        grouped[pid] = pobj
        id_map[pid] = pid
    return grouped, id_map


def normalized_orientation(piece_obj):
    """Return the lexicographically smallest normalized orientation for a piece."""
    try:
        orientations = piece_obj.get_orientations()
        if not orientations:
            if hasattr(piece_obj, 'get_offsets'):
                base = piece_obj.get_offsets()
                base_norm = normalize(tuple(base))
                orientations = [base_norm] if base_norm else []
        if not orientations:
            return []
        best = min(orientations, key=lambda o: _orientation_signature(o))
        return [[i, j] for (i, j) in best]
    except Exception:
        return []
