import logging
import uuid

from flask import Blueprint, request, jsonify

from backend.pieceLibrary import test_piece_library
from backend.utils import VALID_COLORS
from server.services.solver_service import JSONPieceAdapter, group_equivalent_pieces, normalized_orientation
from server.json_storage import (
    current_iso_time,
    load_libraries_index,
    save_libraries_index,
    read_library_pieces,
    write_library_pieces,
    remove_library_file,
)

logger = logging.getLogger(__name__)

libraries_api = Blueprint('libraries_api', __name__)


# ── Internal helpers ────────────────────────────────────────────────────────

def _find_library(library_id):
    for lib in load_libraries_index():
        if lib.get('id') == library_id:
            return lib
    return None


def _add_library(name):
    libraries = load_libraries_index()
    library_id = str(uuid.uuid4())
    now = current_iso_time()
    libraries.append({
        'id': library_id,
        'name': name,
        'editable': True,
        'created_at': now,
        'updated_at': now,
    })
    save_libraries_index(libraries)
    return _find_library(library_id)


def _update_library(library_id, name):
    libraries = load_libraries_index()
    for lib in libraries:
        if lib.get('id') == library_id:
            lib['name'] = name
            lib['updated_at'] = current_iso_time()
            break
    save_libraries_index(libraries)
    return _find_library(library_id)


def _delete_library(library_id):
    libraries = [lib for lib in load_libraries_index() if lib.get('id') != library_id]
    save_libraries_index(libraries)
    remove_library_file(library_id)


def _add_piece(library_id, name, color, cells):
    pieces = read_library_pieces(library_id)
    if any(p.get('library_id') == library_id and p.get('name') == name for p in pieces):
        return None
    # Canonicalize cells at write-time: always store as list of [i, j] lists
    canonical_cells = [[c[0], c[1]] for c in cells]
    pieces.append({
        'library_id': library_id,
        'name': name,
        'color': color,
        'cells': canonical_cells,
    })
    write_library_pieces(library_id, pieces)
    return {'id': name, 'color': color, 'offsets': canonical_cells}


def _delete_piece(library_id, name):
    pieces = [p for p in read_library_pieces(library_id) if not (p.get('library_id') == library_id and p.get('name') == name)]
    write_library_pieces(library_id, pieces)


def _normalize_offsets(raw_offsets):
    """Normalize cell offsets to a consistent [[i, j], ...] format."""
    if not raw_offsets:
        return []
    # Already in the canonical format
    if isinstance(raw_offsets, list) and all(isinstance(pos, list) and len(pos) == 2 for pos in raw_offsets):
        return raw_offsets
    # Tuple-based format from Piece objects
    if isinstance(raw_offsets, (list, tuple)) and all(isinstance(pos, (list, tuple)) and len(pos) == 2 for pos in raw_offsets):
        return [[pos[0], pos[1]] for pos in raw_offsets]
    return []


# ── Routes ──────────────────────────────────────────────────────────────────

@libraries_api.route('/api/libraries', methods=['GET'])
def get_libraries():
    try:
        libraries = load_libraries_index()
        libraries_dict = {lib.get('id'): lib for lib in libraries}
        return jsonify(libraries_dict)
    except Exception as e:
        logger.exception("Failed to get libraries")
        return jsonify({"error": str(e)}), 500


@libraries_api.route('/api/libraries/<library_id>/pieces', methods=['GET'])
def get_library_pieces(library_id):
    try:
        if library_id == 'builtin':
            pieces_dict = {}
            for key, piece in test_piece_library.items():
                pieces_dict[key] = {
                    'id': key,
                    'color': piece.color,
                    'offsets': piece.get_offsets(),
                }
            return jsonify(pieces_dict)

        lib = _find_library(library_id)
        if not lib:
            return jsonify({"error": f"Library with id {library_id} not found"}), 404

        pieces = read_library_pieces(library_id)
        pieces_dict = {}
        for piece in pieces:
            offsets = _normalize_offsets(piece.get('cells') or [])
            color = piece.get('color')
            color = color if color in VALID_COLORS else 'red'
            name = piece.get('name')
            pieces_dict[name] = {
                'id': name,
                'color': color,
                'offsets': offsets,
            }
        return jsonify(pieces_dict)
    except Exception as e:
        logger.exception("Failed to get pieces for library %s", library_id)
        return jsonify({"error": str(e)}), 500


@libraries_api.route('/api/libraries/<library_id>/canonical-pieces', methods=['GET'])
def get_library_canonical_pieces(library_id):
    try:
        if library_id == 'builtin':
            lib = {k: v for k, v in test_piece_library.items()}
        else:
            pieces = read_library_pieces(library_id)
            lib = {p['name']: JSONPieceAdapter(p) for p in pieces}

        grouped, _ = group_equivalent_pieces(lib)
        canonical = []
        for pid, pobj in grouped.items():
            offsets = normalized_orientation(pobj)
            color = getattr(pobj, 'color', None) or 'red'
            canonical.append({
                'color': color,
                'offsets': offsets,
            })
        return jsonify({'pieces': canonical})
    except Exception as e:
        logger.exception("Failed to get canonical pieces for library %s", library_id)
        return jsonify({"error": str(e)}), 500


@libraries_api.route('/api/libraries', methods=['POST'])
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
            "library": library,
        })
    except Exception as e:
        logger.exception("Failed to create library")
        return jsonify({"success": False, "message": str(e)}), 500


@libraries_api.route('/api/libraries/<library_id>', methods=['PUT'])
def update_library(library_id):
    try:
        data_req = request.json
        name = data_req.get('name', '').strip()
        if not name:
            return jsonify({"success": False, "message": "Library name is required"}), 400
        lib = _find_library(library_id)
        if not lib:
            return jsonify({"success": False, "message": f"Library with id {library_id} not found"}), 404
        if not lib.get('editable', True):
            return jsonify({"success": False, "message": "Cannot modify built-in library"}), 403
        library = _update_library(library_id, name)
        return jsonify({
            "success": True,
            "message": "Library updated successfully",
            "library": library,
        })
    except Exception as e:
        logger.exception("Failed to update library %s", library_id)
        return jsonify({"success": False, "message": str(e)}), 500


@libraries_api.route('/api/libraries/<library_id>', methods=['DELETE'])
def delete_library(library_id):
    try:
        lib = _find_library(library_id)
        if not lib:
            return jsonify({"success": False, "message": f"Library with id {library_id} not found"}), 404
        if not lib.get('editable', True):
            return jsonify({"success": False, "message": "Cannot delete built-in library"}), 403
        _delete_library(library_id)
        return jsonify({
            "success": True,
            "message": "Library deleted successfully",
        })
    except Exception as e:
        logger.exception("Failed to delete library %s", library_id)
        return jsonify({"success": False, "message": str(e)}), 500


@libraries_api.route('/api/libraries/<library_id>/pieces', methods=['POST'])
def create_piece(library_id):
    try:
        lib = _find_library(library_id)
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
            "piece": created,
        })
    except Exception as e:
        logger.exception("Failed to create piece in library %s", library_id)
        return jsonify({"success": False, "message": str(e)}), 500


@libraries_api.route('/api/libraries/<library_id>/pieces/<piece_id>', methods=['DELETE'])
def delete_piece(library_id, piece_id):
    try:
        lib = _find_library(library_id)
        if not lib:
            return jsonify({"success": False, "message": f"Library with id {library_id} not found"}), 404
        if not lib.get('editable', True):
            return jsonify({"success": False, "message": "Cannot delete pieces from built-in library"}), 403
        pieces = read_library_pieces(library_id)
        if not any(p.get('name') == piece_id for p in pieces):
            return jsonify({"success": False, "message": f"Piece '{piece_id}' not found in library '{library_id}'"}), 404
        _delete_piece(library_id, piece_id)
        return jsonify({
            "success": True,
            "message": f"Piece '{piece_id}' deleted successfully",
        })
    except Exception as e:
        logger.exception("Failed to delete piece %s from library %s", piece_id, library_id)
        return jsonify({"success": False, "message": str(e)}), 500
