class Board:
    """
    Represents a board (grid) with a given width and height.
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.obstacles = set()  # Track positions that are blocked by obstacles

    def cells(self):
        """
        Returns a list of all board coordinates as (i,j) tuples.
        """
        return [(i, j) for i in range(self.height) for j in range(self.width) if (i, j) not in self.obstacles]

    def in_bounds(self, i, j):
        return 0 <= i < self.height and 0 <= j < self.width and (i, j) not in self.obstacles

    def addObstacles(self, obstacle_positions):
        """
        Add obstacles to the board at specified positions.
        
        Args:
            obstacle_positions: A list of (i, j) tuples representing obstacle positions.
        """
        for position in obstacle_positions:
            i, j = position
            if 0 <= i < self.height and 0 <= j < self.width:
                self.obstacles.add((i, j))
            else:
                raise ValueError(f"Obstacle position {position} is out of bounds.")

    def clearObstacles(self):
        """
        Remove all obstacles from the board.
        """
        self.obstacles.clear()

    def removeObstacle(self, position):
        """
        Remove a specific obstacle from the board.
        
        Args:
            position: An (i, j) tuple representing the obstacle position to remove.
        """
        if position in self.obstacles:
            self.obstacles.remove(position)

    def getObstacles(self):
        """
        Returns a list of all obstacle positions on the board.
        
        Returns:
            A list of (i, j) tuples representing obstacle positions.
        """
        return list(self.obstacles)

    def isObstacle(self, i, j):
        """
        Check if a position is blocked by an obstacle.
        
        Args:
            i: Row coordinate
            j: Column coordinate
            
        Returns:
            True if the position is an obstacle, False otherwise.
        """
        return (i, j) in self.obstacles

    def count_obstacles(self):
        """
        Returns the number of obstacles on the board.
        
        Returns:
            Integer count of obstacles.
        """
        return len(self.obstacles)

    def __str__(self):
        return f"Board({self.height} x {self.width})"
