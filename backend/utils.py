import logging

from backend.board import Board

logger = logging.getLogger(__name__)

# ── Shared color constants ──────────────────────────────────────────────────
# Mapping from color name → colorama Fore code string.
# Lazily imported so that colorama isn't required at import time.
_COLOR_MAPPING = None

VALID_COLORS = frozenset({
    "red", "blue", "green", "yellow", "magenta", "cyan",
    "lightred", "lightblue", "lightgreen", "lightyellow", "lightmagenta", "lightcyan",
    "gray", "purple", "orange", "pink", "salmon", "brown", "white", "black",
    "lightcoral", "lightgoldenrod", "violet", "indigo", "turquoise",
    "brightred", "brightgreen", "brightblue", "brightyellow", "brightpurple",
    "brightorange", "brightmagenta", "brightcyan", "brightbrown", "brightpink",
    "lightorange", "lightpurple", "lightpink",
})


def _get_color_mapping():
    """Lazily import colorama and build the color mapping."""
    global _COLOR_MAPPING
    if _COLOR_MAPPING is not None:
        return _COLOR_MAPPING

    import colorama
    from colorama import Fore
    colorama.init()

    _COLOR_MAPPING = {
        "gray": Fore.LIGHTBLACK_EX,
        "green": Fore.GREEN,
        "red": Fore.RED,
        "blue": Fore.BLUE,
        "white": Fore.WHITE,
        "yellow": Fore.YELLOW,
        "magenta": Fore.MAGENTA,
        "cyan": Fore.CYAN,
        "black": Fore.BLACK,
        "lightred": Fore.LIGHTRED_EX,
        "lightgreen": Fore.LIGHTGREEN_EX,
        "lightblue": Fore.LIGHTBLUE_EX,
        "lightcyan": Fore.LIGHTCYAN_EX,
        "lightmagenta": Fore.LIGHTMAGENTA_EX,
        "lightyellow": Fore.LIGHTYELLOW_EX,
        "brightred": Fore.LIGHTRED_EX,
        "brightgreen": Fore.LIGHTGREEN_EX,
        "brightblue": Fore.LIGHTBLUE_EX,
        "brightcyan": Fore.LIGHTCYAN_EX,
        "brightmagenta": Fore.LIGHTMAGENTA_EX,
        "brightyellow": Fore.LIGHTYELLOW_EX,
        "brightpurple": Fore.LIGHTMAGENTA_EX,
        "brightpink": Fore.LIGHTMAGENTA_EX,
        "brightorange": Fore.LIGHTYELLOW_EX,
        "brightbrown": Fore.LIGHTYELLOW_EX,
        "lightpink": Fore.LIGHTMAGENTA_EX,
        "lightpurple": Fore.LIGHTMAGENTA_EX,
        "lightorange": Fore.LIGHTYELLOW_EX,
        "lightcoral": Fore.LIGHTRED_EX,
        "lightgoldenrod": Fore.LIGHTYELLOW_EX,
        "indigo": Fore.BLUE,
        "violet": Fore.MAGENTA,
        "turquoise": Fore.LIGHTCYAN_EX,
        "pink": Fore.LIGHTMAGENTA_EX,
        "salmon": Fore.LIGHTRED_EX,
        "brown": Fore.RED,
        "purple": Fore.MAGENTA,
        "orange": Fore.YELLOW,
    }
    return _COLOR_MAPPING


# ── Geometry utilities ──────────────────────────────────────────────────────

def normalize(offsets):
    """
    Given a sequence of (i, j) tuples, shift them so that the smallest i and j
    become 0.  Returns a sorted tuple of tuples.
    """
    if not offsets:
        return tuple()
    min_i = min(i for i, j in offsets)
    min_j = min(j for i, j in offsets)
    return tuple(sorted(((i - min_i, j - min_j) for i, j in offsets)))


def compute_orientations(offsets, allow_reflections=True, allow_rotations=True):
    """
    Generate all distinct orientations of a piece described by *offsets*.

    Applies rotations (0°, 90°, 180°, 270°) and optional horizontal
    reflection.  Each orientation is normalized so that the smallest
    coordinate is (0, 0).  Duplicates are removed.

    Parameters
    ----------
    offsets : sequence of (int, int)
        The base piece shape expressed as (row, col) offsets.
    allow_reflections : bool
        Whether to include reflected (mirrored) orientations.
    allow_rotations : bool
        Whether to include rotated orientations.

    Returns
    -------
    list[tuple[tuple[int, int], ...]]
        Distinct orientations, each a tuple of (i, j) pairs.
    """
    base = tuple(offsets)
    if not base:
        return []

    if allow_rotations:
        transforms = [
            lambda i, j: (i, j),
            lambda i, j: (-j, i),
            lambda i, j: (-i, -j),
            lambda i, j: (j, -i),
        ]
    else:
        transforms = [
            lambda i, j: (i, j),
        ]

    seen = set()
    orientation_list = []
    for t in transforms:
        transformed = tuple(t(i, j) for i, j in base)
        norm = normalize(transformed)
        if norm not in seen:
            seen.add(norm)
            orientation_list.append(norm)
        if allow_reflections:
            flipped = tuple((-u, v) for u, v in transformed)
            norm_flipped = normalize(flipped)
            if norm_flipped not in seen:
                seen.add(norm_flipped)
                orientation_list.append(norm_flipped)

    return orientation_list


# ── Display utilities ───────────────────────────────────────────────────────

def print_solution_board(board: Board, solution, piece_library: dict, obstacles=None):
    """
    Prints the board with each cell replaced by the piece id that covers it,
    using ANSI color codes.

    Args:
        board: The Board instance
        solution: List of CandidatePlacement objects
        piece_library: Dictionary mapping piece IDs to Piece objects
        obstacles: Optional list of obstacle positions to display
    """
    from colorama import Style

    color_mapping = _get_color_mapping()

    # Create an empty grid.
    grid = [["." for _ in range(board.width)] for _ in range(board.height)]

    # Mark obstacles
    if obstacles is None and hasattr(board, 'obstacles'):
        obstacles = board.obstacles

    if obstacles:
        for i, j in obstacles:
            if 0 <= i < board.height and 0 <= j < board.width:
                grid[i][j] = ("#", "black")

    # For every candidate placement in the solution, mark its cells.
    if solution:
        for cand in solution:
            piece_color = piece_library[cand.piece_id].color
            for (i, j) in cand.cells:
                if obstacles and (i, j) in obstacles:
                    continue
                grid[i][j] = (cand.piece_id, piece_color)

    # Print the board in color.
    print("\nFinal Tiling:")
    for row in grid:
        row_str_parts = []
        for cell in row:
            if cell == ".":
                row_str_parts.append(".")
            else:
                piece_id, color = cell
                color_code = color_mapping.get(color.lower(), "\033[37m")
                row_str_parts.append(f"{color_code}{piece_id}{Style.RESET_ALL}")
        print(" ".join(row_str_parts))