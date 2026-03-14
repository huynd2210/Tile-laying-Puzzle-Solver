from backend.utils import normalize

class JSONPieceAdapter:
    def __init__(self, piece_dict):
        self.name = piece_dict.get('name')
        self.color = piece_dict.get('color')
        self.cells = piece_dict.get('cells') or []
        self.allow_reflections = piece_dict.get('allow_reflections', True)
        self.allow_rotations = piece_dict.get('allow_rotations', True)

    def get_offsets(self):
        return tuple(tuple(coord) for coord in self.cells)

    def get_orientations(self, allow_reflections=None, allow_rotations=None):
        base = self.get_offsets()
        if not base:
            return []
        use_rot = self.allow_rotations if allow_rotations is None else allow_rotations
        if use_rot:
            transforms = [
                lambda i, j: (i, j),
                lambda i, j: (-j, i),
                lambda i, j: (-i, -j),
                lambda i, j: (j, -i)
            ]
        else:
            transforms = [
                lambda i, j: (i, j)
            ]
        orientations = set()
        orientation_list = []
        for t in transforms:
            transformed = tuple(t(i, j) for i, j in base)
            norm = normalize(transformed)
            if norm not in orientations:
                orientations.add(norm)
                orientation_list.append(norm)
            use_reflect = self.allow_reflections if allow_reflections is None else allow_reflections
            if use_reflect:
                flipped = tuple((-u, v) for u, v in transformed)
                norm_flipped = normalize(flipped)
                if norm_flipped not in orientations:
                    orientations.add(norm_flipped)
                    orientation_list.append(norm_flipped)
        return orientation_list


def _orientation_signature(orientation):
    # orientation: tuple of (i,j)
    coords = sorted(list(orientation))
    return ';'.join(f"{i}:{j}" for i, j in coords)


def _shape_signature(piece_obj):
    try:
        orientations = piece_obj.get_orientations()
        if not orientations:
            # fallback to offsets
            if hasattr(piece_obj, 'get_offsets'):
                base = getattr(piece_obj, 'get_offsets')()
                base_norm = normalize(tuple(base))
                orientations = [base_norm] if base_norm else []
        # Pick lexicographically smallest normalized string among orientations
        sigs = [_orientation_signature(o) for o in orientations]
        return min(sigs) if sigs else ''
    except Exception:
        return ''


def group_equivalent_pieces(piece_lib: dict):
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
    try:
        orientations = piece_obj.get_orientations()
        if not orientations:
            if hasattr(piece_obj, 'get_offsets'):
                base = getattr(piece_obj, 'get_offsets')()
                base_norm = normalize(tuple(base))
                orientations = [base_norm] if base_norm else []
        # Choose canonical orientation by string order
        if not orientations:
            return []
        best = min(orientations, key=lambda o: _orientation_signature(o))
        return [[i, j] for (i, j) in best]
    except Exception:
        return []
