from backend.board import Board
import colorama
from colorama import Fore, Back, Style

# Initialize colorama
colorama.init()

def normalize(offsets):
    """
    Given a list of (i,j) tuples, shift them so that the smallest i and j become 0.
    """
    min_i = min(i for i, j in offsets)
    min_j = min(j for i, j in offsets)
    return tuple(sorted(((i - min_i, j - min_j) for i, j in offsets)))


def print_solution_board(board: Board, solution, piece_library: dict, obstacles=None):
    """
    Prints the board with each cell replaced by the piece id that covers it,
    using ANSI color codes. For example, a cell covered by piece 'D' (with color 'gray')
    will be printed in gray.
    
    Args:
        board: The Board instance
        solution: List of CandidatePlacement objects
        piece_library: Dictionary mapping piece IDs to Piece objects
        obstacles: Optional list of obstacle positions to display
    """
    # Colorama color mapping for common color names
    color_mapping = {
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
        "orange": Fore.YELLOW
    }

    # Create an empty grid.
    grid = [["." for _ in range(board.width)] for _ in range(board.height)]
    
    # Mark obstacles
    if obstacles is None and hasattr(board, 'obstacles'):
        obstacles = board.obstacles
    
    if obstacles:
        for i, j in obstacles:
            if 0 <= i < board.height and 0 <= j < board.width:
                grid[i][j] = ("#", "black")  # Represent obstacles with '#' in black color

    # For every candidate placement in the solution, mark its cells.
    # (We assume no overlapping since the SAT constraints ensure proper tiling.)
    if solution:
        for cand in solution:
            # For this candidate we look up the piece's color.
            piece_color = piece_library[cand.piece_id].color
            for (i, j) in cand.cells:
                # Skip if this is an obstacle position
                if obstacles and (i, j) in obstacles:
                    continue
                # Instead of just the id, store a tuple of (id, color)
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
                color_code = color_mapping.get(color.lower(), Fore.WHITE)
                row_str_parts.append(f"{color_code}{piece_id}{Style.RESET_ALL}")
        print(" ".join(row_str_parts))