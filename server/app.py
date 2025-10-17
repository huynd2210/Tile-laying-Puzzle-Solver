from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import sys
import datetime

# Ensure project root on path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.board import Board
from backend.TilingPuzzle import TilingPuzzle
from backend.pieceLibrary import test_piece_library
from backend.utils import normalize

from server.json_storage import (
    current_iso_time,
    ensure_storage_initialized,
    load_libraries_index,
    save_libraries_index,
    read_library_pieces,
    write_library_pieces,
    add_solution_record,
    list_solution_summaries,
    find_solution_by_id,
)
from server.migrate_db_to_json import export_db_to_json


app = Flask(__name__, static_folder=os.path.join(ROOT_DIR, 'frontend', 'static'), template_folder=os.path.join(ROOT_DIR, 'frontend', 'templates'))
app.secret_key = os.urandom(24)
CORS(app)


def _find_library(data, library_id):
    for lib in data.get('libraries', []):
        if lib.get('id') == library_id:
            return lib
    return None


def _list_libraries_index():
    return load_libraries_index()


def _list_pieces_for_library(library_id):
    return read_library_pieces(library_id)


def _ensure_builtin_library():
    libraries = _list_libraries_index()
    if not any(lib.get('id') == 'builtin' for lib in libraries):
        libraries.append({
            'id': 'builtin',
            'name': 'Built-in Pieces',
            'editable': False,
            'created_at': current_iso_time(),
            'updated_at': current_iso_time()
        })
        save_libraries_index(libraries)


def _add_library(name):
    libraries = _list_libraries_index()
    import uuid
    library_id = str(uuid.uuid4())
    now = current_iso_time()
    libraries.append({
        'id': library_id,
        'name': name,
        'editable': True,
        'created_at': now,
        'updated_at': now
    })
    save_libraries_index(libraries)
    return _find_library(data, library_id)


def _update_library(library_id, name):
    libraries = _list_libraries_index()
    for lib in libraries:
        if lib.get('id') == library_id:
            lib['name'] = name
            lib['updated_at'] = current_iso_time()
            break
    save_libraries_index(libraries)
    return _find_library(data, library_id)


def _delete_library(library_id):
    libraries = [lib for lib in _list_libraries_index() if lib.get('id') != library_id]
    save_libraries_index(libraries)
    # Remove per-library file
    try:
        os.remove(os.path.join(os.path.join(ROOT_DIR, 'instance', 'libraries'), f'{library_id}.json'))
    except Exception:
        pass


def _add_piece(library_id, name, color, cells):
    pieces = read_library_pieces(library_id)
    if any(p.get('library_id') == library_id and p.get('name') == name for p in pieces):
        return None
    pieces.append({
        'library_id': library_id,
        'name': name,
        'color': color,
        'cells': cells
    })
    write_library_pieces(library_id, pieces)
    return {'id': name, 'color': color, 'offsets': cells}


def _delete_piece(library_id, name):
    pieces = [p for p in read_library_pieces(library_id) if not (p.get('library_id') == library_id and p.get('name') == name)]
    write_library_pieces(library_id, pieces)


class JSONPieceAdapter:
    def __init__(self, piece_dict):
        self.name = piece_dict.get('name')
        self.color = piece_dict.get('color')
        self.cells = piece_dict.get('cells') or []

    def get_offsets(self):
        return tuple(tuple(coord) for coord in self.cells)

    def get_orientations(self):
        base = self.get_offsets()
        transforms = [
            lambda i, j: (i, j),
            lambda i, j: (-j, i),
            lambda i, j: (-i, -j),
            lambda i, j: (j, -i)
        ]
        orientations = set()
        orientation_list = []
        for t in transforms:
            transformed = tuple(t(i, j) for i, j in base)
            norm = normalize(transformed)
            if norm not in orientations:
                orientations.add(norm)
                orientation_list.append(norm)
            flipped = tuple((-u, v) for u, v in transformed)
            norm_flipped = normalize(flipped)
            if norm_flipped not in orientations:
                orientations.add(norm_flipped)
                orientation_list.append(norm_flipped)
        return orientation_list


def initialize_storage():
    ROOT_INSTANCE = os.path.join(ROOT_DIR, 'instance')
    db_candidates = [
        os.path.join(ROOT_DIR, 'frontend', 'instance', 'polyomino.db'),
        os.path.join(ROOT_DIR, 'instance', 'polyomino.db'),
    ]
    # Ensure split storage; if monolith exists, migration will handle it
    ensure_storage_initialized()
    # If DB exists but no split storage yet, allow optional DB migration into split monolith path first
    # Skipping automatic DB migration now that split storage exists
    _ensure_builtin_library()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/solve', methods=['POST'])
def solve_puzzle():
    try:
        data = request.json
        width = data.get('width', 4)
        height = data.get('height', 4)
        obstacles = data.get('obstacles', [])
        selected_pieces = data.get('pieces', [])
        library_id = data.get('library_id', 'builtin')
        max_solutions = int(data.get('max_solutions', 1))
        if max_solutions < 1:
            max_solutions = 1
        persist = bool(data.get('persist', False))
        save_name = str(data.get('save_name', '')).strip() or f"Solution {datetime.datetime.utcnow().isoformat()}"

        obstacle_positions = [(i, j) for i, j in obstacles]

        board = Board(width, height)
        if obstacle_positions:
            board.addObstacles(obstacle_positions)

        piece_lib = {}
        if library_id == 'builtin':
            piece_lib = test_piece_library if not selected_pieces else {k: test_piece_library[k] for k in selected_pieces if k in test_piece_library}
        else:
            pieces = _list_pieces_for_library(library_id)
            pdict = {p['name']: JSONPieceAdapter(p) for p in pieces}
            for pid in selected_pieces:
                if pid in pdict:
                    piece_lib[pid] = pdict[pid]

        if not piece_lib:
            return jsonify({'success': False, 'message': 'No valid pieces selected for solving the puzzle.'})

        puzzle = TilingPuzzle(board, piece_lib)
        threads = data.get('threads')
        try:
            threads = int(threads) if threads is not None else None
        except Exception:
            threads = None
        solutions = puzzle.solve(max_solutions=max_solutions, threads=threads)

        if not solutions:
            return jsonify({'success': False, 'message': 'No solution found for the given configuration.'})
        if max_solutions == 1:
            solutions = [solutions]

        serialized = []
        for sol in solutions:
            sdata = []
            for cand in sol:
                color = getattr(piece_lib[cand.piece_id], 'color', None) or 'red'
                sdata.append({
                    'id': cand.piece_id,
                    'color': color,
                    'cells': cand.cells,
                    'orientation': cand.orientation,
                    'position': cand.position
                })
            serialized.append(sdata)

        response_payload = {
            'success': True,
            'solutions': serialized,
            'board': {'width': width, 'height': height, 'obstacles': obstacle_positions}
        }

        if persist:
            try:
                libraries = _list_libraries_index()
                lib = next((l for l in libraries if l.get('id') == library_id), None)
                library_name = lib.get('name') if lib else library_id
                rec = add_solution_record(save_name, {'width': width, 'height': height, 'obstacles': obstacle_positions}, library_id, library_name, selected_pieces, serialized)
                response_payload['saved'] = True
                response_payload['saved_id'] = rec.get('id')
            except Exception as e:
                response_payload['saved'] = False
                response_payload['save_error'] = str(e)

        return jsonify(response_payload)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/api/solutions', methods=['GET'])
def list_solutions():
    try:
        return jsonify({'success': True, 'solutions': list_solution_summaries()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/solutions/<solution_id>', methods=['GET'])
def get_solution(solution_id):
    try:
        rec = find_solution_by_id(solution_id)
        if not rec:
            return jsonify({'success': False, 'message': f'Solution {solution_id} not found'}), 404
        return jsonify({'success': True, 'record': rec})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Libraries API
@app.route('/api/libraries', methods=['GET'])
def get_libraries():
    try:
        libraries = _list_libraries_index()
        libraries_dict = {lib.get('id'): lib for lib in libraries}
        return jsonify(libraries_dict)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/libraries/<library_id>/pieces', methods=['GET'])
def get_library_pieces(library_id):
    try:
        if library_id == 'builtin':
            pieces_dict = {}
            for key, piece in test_piece_library.items():
                pieces_dict[key] = {
                    'id': key,
                    'color': piece.color,
                    'offsets': piece.get_offsets()
                }
            return jsonify(pieces_dict)

        data = {'libraries': _list_libraries_index()}
        lib = _find_library(data, library_id)
        if not lib:
            return jsonify({"error": f"Library with id {library_id} not found"}), 404

        pieces = _list_pieces_for_library(library_id)
        pieces_dict = {}
        for piece in pieces:
            offsets = piece.get('cells') or []
            if isinstance(offsets, tuple) or (isinstance(offsets, list) and any(isinstance(pos, tuple) for pos in offsets)):
                offsets = [[pos[0], pos[1]] for pos in offsets]
            if not all(isinstance(pos, list) for pos in offsets):
                normalized_offsets = []
                try:
                    if isinstance(offsets, list) and len(offsets) % 2 == 0:
                        for i in range(0, len(offsets), 2):
                            normalized_offsets.append([offsets[i], offsets[i+1]])
                except Exception:
                    normalized_offsets = []
            else:
                normalized_offsets = offsets
            # Normalize color: ensure it matches a CSS class we support
            allowed = {
                'red','blue','green','yellow','magenta','cyan','lightred','lightblue','lightgreen','lightyellow','lightmagenta','lightcyan','gray',
                'purple','orange','pink','salmon','brown','white','black','lightcoral','lightgoldenrod','violet','indigo','turquoise',
                'brightred','brightgreen','brightblue','brightyellow','brightpurple','brightorange','brightmagenta','brightcyan','brightbrown','brightpink',
                'lightorange','lightpurple','lightpink'
            }
            color = piece.get('color')
            color = color if color in allowed else 'red'
            name = piece.get('name')
            pieces_dict[name] = {
                'id': name,
                'color': color,
                'offsets': normalized_offsets
            }
        return jsonify(pieces_dict)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/libraries', methods=['POST'])
def create_library():
    try:
        data_req = request.json
        name = data_req.get('name', '').strip()
        if not name:
            return jsonify({"success": False, "message": "Library name is required"}), 400
        library = _add_library(name)
        return jsonify({
            "success": True,
            "message": "Library created successfully",
            "library": library
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/libraries/<library_id>', methods=['PUT'])
def update_library(library_id):
    try:
        data_req = request.json
        name = data_req.get('name', '').strip()
        if not name:
            return jsonify({"success": False, "message": "Library name is required"}), 400
        data = _load_data()
        lib = _find_library(data, library_id)
        if not lib:
            return jsonify({"success": False, "message": f"Library with id {library_id} not found"}), 404
        if not lib.get('editable', True):
            return jsonify({"success": False, "message": "Cannot modify built-in library"}), 403
        library = _update_library(library_id, name)
        return jsonify({
            "success": True,
            "message": "Library updated successfully",
            "library": library
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/libraries/<library_id>', methods=['DELETE'])
def delete_library(library_id):
    try:
        data = _load_data()
        lib = _find_library(data, library_id)
        if not lib:
            return jsonify({"success": False, "message": f"Library with id {library_id} not found"}), 404
        if not lib.get('editable', True):
            return jsonify({"success": False, "message": "Cannot delete built-in library"}), 403
        _delete_library(library_id)
        return jsonify({
            "success": True,
            "message": "Library deleted successfully"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/libraries/<library_id>/pieces', methods=['POST'])
def create_piece(library_id):
    try:
        data = _load_data()
        lib = _find_library(data, library_id)
        if not lib:
            return jsonify({"success": False, "message": f"Library with id {library_id} not found"}), 404
        if not lib.get('editable', True):
            return jsonify({"success": False, "message": "Cannot add pieces to built-in library"}), 403

        data_req = request.json
        name = data_req.get('name', '').strip()
        color = data_req.get('color', '').strip()
        cells = data_req.get('cells', [])
        if not name:
            return jsonify({"success": False, "message": "Piece name is required"}), 400
        if not color:
            return jsonify({"success": False, "message": "Piece color is required"}), 400
        if not cells or not isinstance(cells, list) or len(cells) == 0:
            return jsonify({"success": False, "message": "Piece must have at least one cell"}), 400

        created = _add_piece(library_id, name, color, cells)
        if created is None:
            return jsonify({"success": False, "message": f"Piece '{name}' already exists in this library"}), 400
        return jsonify({
            "success": True,
            "message": "Piece created successfully",
            "piece": created
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/libraries/<library_id>/pieces/<piece_id>', methods=['DELETE'])
def delete_piece(library_id, piece_id):
    try:
        data = _load_data()
        lib = _find_library(data, library_id)
        if not lib:
            return jsonify({"success": False, "message": f"Library with id {library_id} not found"}), 404
        if not lib.get('editable', True):
            return jsonify({"success": False, "message": "Cannot delete pieces from built-in library"}), 403
        pieces = _list_pieces_for_library(data, library_id)
        if not any(p.get('name') == piece_id for p in pieces):
            return jsonify({"success": False, "message": f"Piece '{piece_id}' not found in library '{library_id}'"}), 404
        _delete_piece(library_id, piece_id)
        return jsonify({
            "success": True,
            "message": f"Piece '{piece_id}' deleted successfully"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    initialize_storage()
    app.run(debug=True)


