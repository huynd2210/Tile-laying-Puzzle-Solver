from board import Board
from TilingPuzzle import TilingPuzzle
from piece import Piece
from utils import print_solution_board

def test_obstacle_colors():
    """Test the obstacle functionality with colorama colors."""
    # Create a small board with some obstacles
    board = Board(4, 4)
    obstacles = [(0, 0), (1, 1), (2, 2), (3, 3)]  # Diagonal pattern
    board.addObstacles(obstacles)
    
    print(f"Created a {board} with obstacles at {obstacles}")
    
    # Create a custom piece library with pieces that can cover the board
    piece_lib = {
        'A': Piece(0, 0, 0, 1, 1, 0, color="red"),      # L-shape
        'B': Piece(0, 0, 0, 1, 1, 1, color="blue"),     # Corner piece
        'C': Piece(0, 0, 0, 1, color="green"),          # Domino
        'D': Piece(0, 0, 1, 0, color="yellow"),         # Domino (horizontal)
        'E': Piece(0, 0, color="magenta"),              # Single cell
        'F': Piece(0, 0, color="cyan"),                 # Single cell
        'G': Piece(0, 0, color="lightred"),             # Single cell
        'H': Piece(0, 0, color="lightgreen"),           # Single cell
        'I': Piece(0, 0, color="lightblue"),            # Single cell
        'J': Piece(0, 0, color="lightyellow"),          # Single cell
        'K': Piece(0, 0, color="lightmagenta"),         # Single cell
        'L': Piece(0, 0, color="lightcyan")             # Single cell
    }
    
    # Create a puzzle and solve it
    puzzle = TilingPuzzle(board, piece_lib)
    solution = puzzle.solve()
    
    if solution:
        print("\nSolution found! Here is the board with colors:")
        print_solution_board(board, solution, piece_lib)
        
        # Print which pieces were used
        print("\nPieces used in solution:")
        for cand in solution:
            print(f"Piece {cand.piece_id}: color={piece_lib[cand.piece_id].color}, covering {cand.cells}")
    else:
        print("No solution found, but let's still display the board with obstacles:")
        print_solution_board(board, [], piece_lib)

if __name__ == "__main__":
    test_obstacle_colors() 