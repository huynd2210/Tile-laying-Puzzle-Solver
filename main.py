from TilingPuzzle import TilingPuzzle
from board import Board
from pieceLibrary import test_piece_library, patchworkPieceLibrary
from utils import print_solution_board


def main():
    # Define board dimensions that exactly cover the total area of the pieces.
    # For instance, if the pieces cover 2 + 3 + 4 + 3 = 12 cells, we use a 3x4 board.
    board = Board(width=4, height=3)
    print("Board:", board)

    # Create the tiling puzzle instance.
    piece_lib = test_piece_library
    puzzle = TilingPuzzle(board, piece_lib)
    print(f"Generated {len(puzzle.candidates)} candidate placements.")

    # Solve the puzzle.
    print("Solving the puzzle ...")
    solution = puzzle.solve()

    if solution is not None:
        print("\nA valid tiling has been found. The placements are:")
        for cand in solution:
            print(" ", cand)
        # Print the board with piece ids.
        print_solution_board(board, solution, piece_lib)
    else:
        print("No solution found for the given puzzle.")


def main_with_obstacles():
    """Demonstrate solving a puzzle with obstacles."""
    # Create a board
    board = Board(width=4, height=3)
    
    # Add obstacles that form an interesting pattern
    obstacles = [(0, 0), (0, 3), (1, 3)]
    print(f"Adding obstacles at positions: {obstacles}")
    board.addObstacles(obstacles)
    
    print(f"Board {board} with {board.count_obstacles()} obstacles")
    print(f"Obstacle positions from board: {board.getObstacles()}")

    # Debug: Check if obstacles are correctly registered
    for i in range(board.height):
        for j in range(board.width):
            if board.isObstacle(i, j):
                print(f"Position ({i}, {j}) is an obstacle")
    
    # Let's also check what cells are considered valid by the board
    valid_cells = board.cells()
    print(f"Valid cells: {valid_cells}")
    print(f"Total valid cells: {len(valid_cells)}")

    # Create the tiling puzzle instance with our piece library
    piece_lib = test_piece_library
    puzzle = TilingPuzzle(board, piece_lib)
    print(f"Generated {len(puzzle.candidates)} candidate placements.")
    
    # Debug: Check a few candidate placements to ensure they don't cover obstacles
    if puzzle.candidates:
        print("\nSample candidate placements:")
        for i, cand in enumerate(puzzle.candidates[:5]):  # Show first 5 candidates
            print(f"  {cand}")
            # Check if any cells overlap with obstacles
            for cell in cand.cells:
                if cell in board.obstacles:
                    print(f"    WARNING: Candidate covers obstacle at {cell}")

    # Solve the puzzle
    print("\nSolving the puzzle with obstacles...")
    solution = puzzle.solve()

    if solution is not None:
        print("\nA valid tiling has been found. The placements are:")
        for cand in solution:
            print(" ", cand)
            # Check if any cells in the solution overlap with obstacles
            for cell in cand.cells:
                if cell in board.obstacles:
                    print(f"    ERROR: Solution piece covers obstacle at {cell}")
        
        # Print the board with piece ids, showing obstacles as '#'
        print_solution_board(board, solution, piece_lib)
        
        # Additional verification
        covered_cells = set()
        for cand in solution:
            covered_cells.update(cand.cells)
        
        # Ensure no obstacles are covered
        obstacle_intersect = covered_cells.intersection(board.obstacles)
        if obstacle_intersect:
            print(f"ERROR: Solution covers obstacles at: {obstacle_intersect}")
        
        # Ensure all non-obstacle cells are covered
        expected_cells = {(i, j) for i in range(board.height) for j in range(board.width) 
                          if (i, j) not in board.obstacles}
        uncovered_cells = expected_cells - covered_cells
        if uncovered_cells:
            print(f"WARNING: Some non-obstacle cells are not covered: {uncovered_cells}")
    else:
        print("No solution found for the given puzzle with obstacles.")


def patchwork():
    board = Board(width=9, height=9)
    print("Board:", board)

    # Create the tiling puzzle instance.
    piece_lib = patchworkPieceLibrary
    puzzle = TilingPuzzle(board, piece_lib)
    print(f"Generated {len(puzzle.candidates)} candidate placements.")

    # Solve the puzzle.
    print("Solving the puzzle ...")
    solution = puzzle.solve()

    if solution is not None:
        print("\nA valid tiling has been found. The placements are:")
        for cand in solution:
            print(" ", cand)
        # Print the board with piece ids.
        print_solution_board(board, solution, piece_lib)
    else:
        print("No solution found for the given puzzle.")


if __name__ == '__main__':
    # print("=== Standard Puzzle ===")
    # main()
    # print("\n=== Puzzle with Obstacles ===")
    # main_with_obstacles()
    patchwork()

