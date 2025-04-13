class Coordinate:
    def __init__(self, i, j):
        self.i = i
        self.j = j

    def __repr__(self):
        return f"({self.i},{self.j})"

    def __iter__(self):
        yield self.i
        yield self.j