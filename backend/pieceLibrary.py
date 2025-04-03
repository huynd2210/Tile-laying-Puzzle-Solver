from backend.piece import Piece

#Piece are defined as follows (example):
#Piece(i1, j1, i2, j2, i3, j3 ...etc, color="white")
#A piece contains the coordinates in which the piece is placed from
#Imagine if the piece was placed at the top left corner of the board (0,0)
#The coordinates are then the cells in the board the piece would cover.
mainPieceLibrary = {
    "a" : Piece(0,0,0,1,1,1, color="red"),
    "b" : Piece(0,0,1,0,1,1, color="blue"),
    "c" : Piece(0,0,0,1,1,1, color="green"),
    "d" : Piece(0,0,1,0,1,1, color="yellow"),
    "e" : Piece(0,0,0,1,1,0,1,1, color="purple"),
    "f" : Piece(0,0,0,1,1,0,1,1, color="orange"),
    "g" : Piece(0,0,0,1,1,0,1,1, color="cyan"),
    "h" : Piece(0,0,0,1,1,0,1,1, color="magenta"),
    "i" : Piece(0,0,0,1, color="pink"),
    "j" : Piece(0, 0, 1, 0, color="salmon"),
    "0" : Piece(0,0,0,1, color="brown"),
    "1" : Piece(0,0,0,1, color="white"),
    "2" : Piece(0,0,0,1, color="black"),
    "3" : Piece(0,0,0,1,0,2,0,3, color="lightblue"),
    "4" : Piece(0,0,0,1,0,2,0,3, color="lightgreen"),
    "5" : Piece(0,0,0,1,0,2,1,2, color="lightcoral"),
    "6" : Piece(0,0,0,1,1,0,1,1,1,2, color="lightgoldenrod"),
    "7" : Piece(0,0,1,0, color="violet"),
    "8" : Piece(0,0,1,0, color="indigo"),
    "9" : Piece(0,0,1,0, color="turquoise"),
}

patchworkPieceLibrary = {
    "a" : Piece(0,1,1,0,1,1,1,2,1,3,2,1, color="red"), #0 3
    "b" : Piece(0,0,0,1,0,2,0,3,0,4, color="blue"), #7 1
    "c" : Piece(0,1,1,1,2,1,3,0,3,1,3,2, color="green"), #7 2
    "d" : Piece(0,1,1,0,1,1,1,2,2,0,2,1,2,2,3,1, color="yellow"), #5 3
    "e" : Piece(0,1,1,1,1,2,2,0,2,1,3,1, color="purple"), #2 1
    "f": Piece(0,1,1,0,1,1,1,2,2,0,2,2, color="orange"), #3 6
    "g": Piece(0,1,1,0,1,1,2,0, color="magenta"), #3 2
    "h": Piece(0,0,0,1,0,2,2,1,3,1, color="pink"), #2 3
    "i": Piece(0,1,1,1,1,2,0,2, color="cyan"), #4 2
    "j": Piece(0,1,0,2,1,0,1,1,1,2,1,3, color="brown"), #7 4
    "k": Piece(0,2,0,1,1,1,1,2,1,3,1,4,2,2, color="gray"), #1 4
    "l": Piece(0,2,1,1,1,2,2,0,2,1, color="white"), #10 4
    "m": Piece(0,1,1,1,2,0,2,1,3,0,3,1, color="brightred"), #10 5
    "n": Piece(0,3,1,0,1,1,1,2,1,3,2,0, color="brightgreen"), #1 2
    "o": Piece(0,0,0,1,1,1,2,1,3,0,3,1, color="brightblue"), #1 5
    "q": Piece(0,0,1,0,1,1,2,0,2,1,3,1, color="brightyellow"), #4 2
    "r": Piece(0,1,1,1,2,1,3,0,3,1, color="brightpurple"), #10 3
    "s": Piece(0,1,1,0,1,1,1,2,1,3, color="brightorange"), #3 4
    "t": Piece(0,1,1,0,1,1,1,2,2,1, color="brightmagenta"), #5 4
    "u": Piece(0,0,0,1,1,0,1,1,2,1,2,2, color="brightcyan"), #8,6
    "v": Piece(0,0,0,1,0,2,0,3, color="brightbrown"), #3 3
    "w": Piece(0,0,0,1,0,2,1,0,1,2, color="brightpink"),#1 2
    "x": Piece(0,1,1,1,2,0,2,1,2,2, color="black"),#5 5
    "y": Piece(0,1,1,0,1,1,2,0,2,1, color="lightred"), #2 2
    "z": Piece(0,1,1,1,2,0,2,1, color="lightgreen"), #4 6
    "0": Piece(0,0,0,1,1,1,1,2, color="lightblue"), #7 6
    "1": Piece(0,0,0,1,1,0,1,1, color="lightpink"), #6 5
    "2": Piece(0,0,0,1, color="lightyellow"), #2 1
    "3": Piece(0,0,1,0,1,1, color="lightcyan"), #3 1
    "4": Piece(0,1,1,0,1,1,2,1, color="lightmagenta"), #2 2
    "5": Piece(0,0,0,2,1,0,1,1,1,2,2,0,2,2, color="lightorange"), #2 3
    "6": Piece(0,0,0,1,0,2, color="lightgreen"), #2 2
    "7": Piece(0,1,1,0,1,1, color="lightpurple"), #1 3
}

test_piece_library = {
    # Domino piece (2 cells)
    "D": Piece(0,0, 0,1, color="gray"),
    # An "L" tromino (3 cells)
    "L": Piece(0,0, 0,1, 1,0, color="red"),
    # A square tetromino (O-tetromino)
    "O": Piece(0,0, 0,1, 1,0, 1,1, color="blue"),
    # A straight triomino (I-triomino)
    "I": Piece(0,0, 1,0, 2,0, color="green"),
    "U": Piece(0,0, 1,0, 1,1, 1,2,0,2, color="yellow"),
}