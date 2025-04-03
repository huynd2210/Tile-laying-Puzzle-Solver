from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import json
import os
import uuid
import datetime
import sys

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON

from backend.board import Board
from backend.piece import Piece as PythonPiece  # Renaming to avoid confusion
from backend.TilingPuzzle import TilingPuzzle
from backend.pieceLibrary import test_piece_library
from backend.utils import normalize  # For normalizing piece orientations

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.urandom(24)  # Required for session management
CORS(app)  # Enable CORS for all routes
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/polyomino.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database models
class Library(db.Model):
    __tablename__ = 'libraries'
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    editable = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    pieces = relationship('Piece', back_populates='library', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'editable': self.editable,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Piece(db.Model):
    __tablename__ = 'pieces'
    
    id = Column(Integer, primary_key=True)
    library_id = Column(String(36), ForeignKey('libraries.id'), nullable=False)
    name = Column(String(10), nullable=False)
    color = Column(String(50), nullable=False)
    cells = Column(JSON, nullable=False)  # Store the cell offsets as JSON
    
    library = relationship('Library', back_populates='pieces')
    
    def to_dict(self):
        return {
            'id': self.name,
            'color': self.color,
            'offsets': self.cells
        }

# Create built-in pieces
builtin_pieces = {
    "I": {"color": "red", "offsets": [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4]]},  # I pentomino
    "L": {"color": "blue", "offsets": [[0, 0], [1, 0], [2, 0], [3, 0], [3, 1]]},  # L pentomino
    "P": {"color": "green", "offsets": [[0, 0], [0, 1], [1, 0], [1, 1], [2, 0]]},  # P pentomino
    "N": {"color": "yellow", "offsets": [[0, 0], [0, 1], [1, 1], [1, 2], [1, 3]]},  # N pentomino
    "T": {"color": "magenta", "offsets": [[0, 0], [0, 1], [0, 2], [1, 1], [2, 1]]},  # T pentomino
    "U": {"color": "cyan", "offsets": [[0, 0], [0, 2], [1, 0], [1, 1], [1, 2]]},  # U pentomino
    "V": {"color": "lightred", "offsets": [[0, 0], [1, 0], [2, 0], [2, 1], [2, 2]]},  # V pentomino
    "W": {"color": "lightblue", "offsets": [[0, 0], [1, 0], [1, 1], [2, 1], [2, 2]]},  # W pentomino
    "X": {"color": "lightgreen", "offsets": [[0, 1], [1, 0], [1, 1], [1, 2], [2, 1]]},  # X pentomino
    "Y": {"color": "lightyellow", "offsets": [[0, 1], [1, 0], [1, 1], [2, 1], [3, 1]]},  # Y pentomino
    "Z": {"color": "lightmagenta", "offsets": [[0, 0], [0, 1], [1, 1], [2, 1], [2, 2]]},  # Z pentomino
    "F": {"color": "lightcyan", "offsets": [[0, 1], [1, 0], [1, 1], [1, 2], [2, 0]]}   # F pentomino
}

# Adapter class for database Piece model to work with TilingPuzzle
class PieceAdapter:
    """
    Adapter class that wraps database Piece objects to add necessary methods
    for use with the TilingPuzzle solver.
    """
    def __init__(self, db_piece):
        self.db_piece = db_piece
        self.color = db_piece.color
        self.cells = db_piece.cells
    
    def get_offsets(self):
        """Returns the offsets as a tuple of (i,j) pairs."""
        return tuple(tuple(coord) for coord in self.cells)
    
    def get_orientations(self):
        """
        Generate all distinct orientations of the piece.
        
        The routine applies rotations (0, 90, 180, 270 degrees) and reflection (flipping horizontally)
        to produce possible orientations. Each orientation is normalized so that the smallest coordinate
        is (0,0). Duplicate orientations are removed.
        
        Returns a list of orientations. Each orientation is a tuple of (i,j) offset pairs.
        """
        base = self.get_offsets()
        # Define transformation functions:
        # identity, rotate 90: (i,j) -> (-j, i), rotate 180: (i,j) -> (-i, -j),
        # rotate 270: (i,j) -> (j, -i)
        transforms = [
            lambda i, j: (i, j),
            lambda i, j: (-j, i),
            lambda i, j: (-i, -j),
            lambda i, j: (j, -i)
        ]
        # For each transform, also consider horizontal flip (mirroring j coordinate)
        orientations = set()
        orientation_list = []
        for t in transforms:
            transformed = tuple(t(i, j) for i, j in base)
            norm = normalize(transformed)
            if norm not in orientations:
                orientations.add(norm)
                orientation_list.append(norm)
            # Apply horizontal flip on top of the transformation.
            flipped = tuple((-u, v) for u, v in transformed)
            norm_flipped = normalize(flipped)
            if norm_flipped not in orientations:
                orientations.add(norm_flipped)
                orientation_list.append(norm_flipped)
        return orientation_list

def initialize_database():
    """Initialize the database with built-in pieces"""
    # Create tables
    with app.app_context():
        db.create_all()
        
        # Check if built-in library already exists
        builtin = Library.query.filter_by(id='builtin').first()
        if not builtin:
            # Create built-in library
            builtin = Library(
                id='builtin',
                name='Built-in Pieces',
                editable=False
            )
            db.session.add(builtin)
            
            # Add built-in pieces
            for piece_id, piece_data in builtin_pieces.items():
                piece = Piece(
                    library_id='builtin',
                    name=piece_id,
                    color=piece_data['color'],
                    cells=piece_data['offsets']
                )
                db.session.add(piece)
            
            db.session.commit()
            print("Initialized database with built-in pieces")

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')

@app.route('/api/solve', methods=['POST'])
def solve_puzzle():
    """API endpoint to solve a polyomino puzzle."""
    try:
        # Get data from request
        data = request.json
        width = data.get('width', 4)
        height = data.get('height', 4)
        obstacles = data.get('obstacles', [])
        selected_pieces = data.get('pieces', [])
        library_id = data.get('library_id', 'builtin')
        
        # Convert obstacles from array indices to (i,j) coordinates
        obstacle_positions = []
        for obs in obstacles:
            i, j = obs
            obstacle_positions.append((i, j))
        
        # Create board and add obstacles
        board = Board(width, height)
        if obstacle_positions:
            board.addObstacles(obstacle_positions)
        
        # Create piece library
        piece_lib = {}
        
        # Check which library to use
        if library_id == 'builtin':
            # Use the built-in test library
            if not selected_pieces:
                # If no pieces are specified, use all available pieces
                piece_lib = test_piece_library
            else:
                # Use only the selected pieces
                piece_lib = {key: test_piece_library[key] for key in selected_pieces if key in test_piece_library}
        else:
            # Get custom pieces from specific library
            pieces = Piece.query.filter_by(library_id=library_id).all()
            piece_dict = {piece.name: PieceAdapter(piece) for piece in pieces}  # Use adapter for database pieces
            
            for piece_id in selected_pieces:
                if piece_id in piece_dict:
                    piece_lib[piece_id] = piece_dict[piece_id]
        
        # Check if we have any pieces to work with
        if not piece_lib:
            return jsonify({
                'success': False,
                'message': 'No valid pieces selected for solving the puzzle.'
            })
            
        # Create puzzle and solve
        puzzle = TilingPuzzle(board, piece_lib)
        solution = puzzle.solve()
        
        if solution:
            # Convert solution to a format suitable for the frontend
            solution_data = []
            for cand in solution:
                piece_data = {
                    'id': cand.piece_id,
                    'color': piece_lib[cand.piece_id].color,
                    'cells': cand.cells,
                    'orientation': cand.orientation,
                    'position': cand.position
                }
                solution_data.append(piece_data)
            
            return jsonify({
                'success': True,
                'solution': solution_data,
                'board': {
                    'width': width,
                    'height': height,
                    'obstacles': obstacle_positions
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No solution found for the given configuration.'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/api/pieces', methods=['GET'])
def get_pieces():
    """Return the available built-in pieces."""
    pieces = {}
    for key, piece in test_piece_library.items():
        pieces[key] = {
            'id': key,
            'color': piece.color,
            'offsets': piece.get_offsets()
        }
    return jsonify(pieces)

@app.route('/api/libraries', methods=['GET'])
def get_libraries():
    """Return all available piece libraries."""
    try:
        libraries = Library.query.all()
        print(f"Found {len(libraries)} libraries in the database:")
        for lib in libraries:
            print(f"  ID: {lib.id}, Name: {lib.name}, Editable: {lib.editable}")
        
        # Filter out the patchwork_pieces library
        filtered_libraries = [lib for lib in libraries if lib.id != 'patchwork_pieces' and lib.id != 'main_pieces']
        print(f"After filtering, returning {len(filtered_libraries)} libraries")
        
        libraries_dict = {library.id: library.to_dict() for library in filtered_libraries}
        
        return jsonify(libraries_dict)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/libraries/<library_id>/pieces', methods=['GET'])
def get_library_pieces(library_id):
    try:
        pieces = Piece.query.filter_by(library_id=library_id).all()
        
        # If no pieces found for this library, check if library exists
        if not pieces and not Library.query.filter_by(id=library_id).first():
            return jsonify({"error": f"Library with id {library_id} not found"}), 404
        
        pieces_dict = {}
        for piece in pieces:
            # Debug piece data
            print(f"Processing piece {piece.name}: color={piece.color}, cells={piece.cells}")
            
            # Ensure we have a valid list of offsets
            offsets = piece.cells
            
            # Ensure offsets are in the correct format [[row, col], [row, col], ...]
            if offsets:
                # Handle tuples
                if isinstance(offsets, tuple) or (isinstance(offsets, list) and any(isinstance(pos, tuple) for pos in offsets)):
                    offsets = [[pos[0], pos[1]] for pos in offsets]
                
                # Ensure all offsets are lists
                if all(isinstance(pos, list) for pos in offsets):
                    normalized_offsets = offsets
                else:
                    # Try to normalize other formats
                    normalized_offsets = []
                    try:
                        if len(offsets) % 2 == 0:  # Could be flat array
                            for i in range(0, len(offsets), 2):
                                normalized_offsets.append([offsets[i], offsets[i+1]])
                    except:
                        # If we can't normalize, use an empty list
                        normalized_offsets = []
                        print(f"Warning: Couldn't normalize offsets for piece {piece.name}: {offsets}")
            else:
                normalized_offsets = []
                print(f"Warning: Empty offsets for piece {piece.name}")
            
            # Ensure color is present and valid
            color = piece.color if piece.color else 'red'  # Default to red if no color
            
            # Debug the final piece data being sent to frontend
            print(f"Final piece {piece.name} data: color={color}, offsets={normalized_offsets}")
            
            pieces_dict[piece.name] = {
                'id': piece.name,
                'color': color,
                'offsets': normalized_offsets
            }
        
        print(f"Returning {len(pieces_dict)} pieces for library {library_id}")
        return jsonify(pieces_dict)
    except Exception as e:
        print(f"Error in get_library_pieces: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/libraries', methods=['POST'])
def create_library():
    """Create a new custom piece library."""
    try:
        data = request.json
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({"success": False, "message": "Library name is required"}), 400
        
        # Generate a unique ID
        library_id = str(uuid.uuid4())
        
        # Create new library
        library = Library(
            id=library_id,
            name=name,
            editable=True
        )
        
        db.session.add(library)
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": "Library created successfully",
            "library": library.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/libraries/<library_id>', methods=['PUT'])
def update_library(library_id):
    """Update a library's properties."""
    try:
        library = Library.query.filter_by(id=library_id).first()
        
        if not library:
            return jsonify({"success": False, "message": f"Library with id {library_id} not found"}), 404
        
        if not library.editable:
            return jsonify({"success": False, "message": "Cannot modify built-in library"}), 403
        
        data = request.json
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({"success": False, "message": "Library name is required"}), 400
        
        library.name = name
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": "Library updated successfully",
            "library": library.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/libraries/<library_id>', methods=['DELETE'])
def delete_library(library_id):
    """Delete a custom library."""
    try:
        library = Library.query.filter_by(id=library_id).first()
        
        if not library:
            return jsonify({"success": False, "message": f"Library with id {library_id} not found"}), 404
        
        if not library.editable:
            return jsonify({"success": False, "message": "Cannot delete built-in library"}), 403
        
        db.session.delete(library)
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": "Library deleted successfully"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/libraries/<library_id>/pieces', methods=['POST'])
def create_piece(library_id):
    """Create a new piece in a library."""
    try:
        library = Library.query.filter_by(id=library_id).first()
        
        if not library:
            return jsonify({"success": False, "message": f"Library with id {library_id} not found"}), 404
        
        if not library.editable:
            return jsonify({"success": False, "message": "Cannot add pieces to built-in library"}), 403
        
        data = request.json
        name = data.get('name', '').strip()
        color = data.get('color', '').strip()
        cells = data.get('cells', [])
        
        if not name:
            return jsonify({"success": False, "message": "Piece name is required"}), 400
        
        if not color:
            return jsonify({"success": False, "message": "Piece color is required"}), 400
        
        if not cells or not isinstance(cells, list) or len(cells) == 0:
            return jsonify({"success": False, "message": "Piece must have at least one cell"}), 400
        
        # Check if piece with this name already exists in the library
        existing_piece = Piece.query.filter_by(library_id=library_id, name=name).first()
        if existing_piece:
            return jsonify({"success": False, "message": f"Piece '{name}' already exists in this library"}), 400
        
        # Create new piece
        piece = Piece(
            library_id=library_id,
            name=name,
            color=color,
            cells=cells
        )
        
        db.session.add(piece)
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": "Piece created successfully",
            "piece": piece.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/libraries/<library_id>/pieces/<piece_id>', methods=['DELETE'])
def delete_piece(library_id, piece_id):
    """Delete a piece from a library."""
    try:
        library = Library.query.filter_by(id=library_id).first()
        
        if not library:
            return jsonify({"success": False, "message": f"Library with id {library_id} not found"}), 404
        
        if not library.editable:
            return jsonify({"success": False, "message": "Cannot delete pieces from built-in library"}), 403
        
        piece = Piece.query.filter_by(library_id=library_id, name=piece_id).first()
        
        if not piece:
            return jsonify({"success": False, "message": f"Piece '{piece_id}' not found in library '{library_id}'"}), 404
        
        db.session.delete(piece)
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": f"Piece '{piece_id}' deleted successfully"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True) 