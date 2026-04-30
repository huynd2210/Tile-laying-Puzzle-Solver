import datetime
import logging

from flask import Blueprint, request, jsonify

from backend.board import Board
from backend.TilingPuzzle import TilingPuzzle
from backend.PySatSolver import PySatSolver
from backend.pieceLibrary import test_piece_library
from server.services.solver_service import JSONPieceAdapter, group_equivalent_pieces
from server.json_storage import (
    read_library_pieces,
    add_solution_record,
    list_solution_summaries,
    find_solution_by_id,
    load_libraries_index,
    current_iso_time,
)

logger = logging.getLogger(__name__)

solve_api = Blueprint('solve_api', __name__)

# ── Constants ───────────────────────────────────────────────────────────────

MAX_BOARD_DIMENSION = 100  # Reasonable upper limit for board width/height


# ── Helper functions (decomposed from solve_puzzle) ─────────────────────────

def _parse_solve_request(data):
    """Parse and validate the incoming solve request payload."""
    width = data.get('width', 4)
    height = data.get('height', 4)

    # Validate board dimensions
    if not isinstance(width, int) or not isinstance(height, int):
        raise ValueError("Board width and height must be integers.")
    if width < 1 or height < 1:
        raise ValueError("Board width and height must be positive.")
    if width > MAX_BOARD_DIMENSION or height > MAX_BOARD_DIMENSION:
        raise ValueError(f"Board dimensions must not exceed {MAX_BOARD_DIMENSION}.")

    obstacles = data.get('obstacles', [])
    selected_pieces = data.get('pieces', [])
    library_id = data.get('library_id', 'builtin')

    try:
        max_solutions = int(data.get('max_solutions', 1))
    except (ValueError, TypeError):
        max_solutions = 1

    persist = bool(data.get('persist', False))
    save_name = (
        str(data.get('save_name', '')).strip()
        or f"Solution {current_iso_time()}"
    )
    dedupe_equivalent = bool(data.get('dedupe_equivalent', True))
    allow_reflections = data.get('allow_reflections', True)
    allow_rotations = data.get('allow_rotations', True)

    try:
        threads = int(data.get('threads')) if data.get('threads') is not None else None
    except (ValueError, TypeError):
        threads = None

    return {
        'width': width,
        'height': height,
        'obstacles': [(i, j) for i, j in obstacles],
        'selected_pieces': selected_pieces,
        'library_id': library_id,
        'max_solutions': max_solutions,
        'persist': persist,
        'save_name': save_name,
        'dedupe_equivalent': dedupe_equivalent,
        'allow_reflections': allow_reflections,
        'allow_rotations': allow_rotations,
        'threads': threads,
    }


def _build_piece_library(library_id, selected_pieces, allow_reflections, allow_rotations):
    """Build the piece library dict from the library_id and selected piece keys."""
    piece_lib = {}
    if library_id == 'builtin':
        piece_lib = (
            test_piece_library if not selected_pieces
            else {k: test_piece_library[k] for k in selected_pieces if k in test_piece_library}
        )
    else:
        pieces = read_library_pieces(library_id)
        pdict = {
            p['name']: JSONPieceAdapter({
                **p,
                'allow_reflections': allow_reflections,
                'allow_rotations': allow_rotations,
            })
            for p in pieces
        }
        for pid in selected_pieces:
            if pid in pdict:
                piece_lib[pid] = pdict[pid]
    return piece_lib


def _prepare_solver_library(piece_lib, selected_pieces, dedupe_equivalent,
                             library_id, allow_reflections, allow_rotations):
    """Optionally dedupe equivalent pieces and prepare the library for the solver."""
    lib_for_solver = piece_lib
    canonical_of = {pid: pid for pid in piece_lib.keys()}

    if dedupe_equivalent:
        lib_for_solver, canonical_of = group_equivalent_pieces(piece_lib)

    # Build reverse mapping: canonical_id → original display id
    rep_of = {}
    for pid in selected_pieces:
        canon = canonical_of.get(pid, pid)
        if canon not in rep_of:
            rep_of[canon] = pid
    for pid, canon in canonical_of.items():
        rep_of.setdefault(canon, pid)

    # Wrap built-in pieces in JSONPieceAdapter when orientation flags are non-default
    if library_id == 'builtin' and (allow_reflections is False or allow_rotations is False):
        lib_for_solver = {
            pid: JSONPieceAdapter({
                'name': pid,
                'color': getattr(p, 'color', None),
                'cells': [[i, j] for (i, j) in (p.get_offsets() if hasattr(p, 'get_offsets') else [])],
                'allow_reflections': allow_reflections,
                'allow_rotations': allow_rotations,
            })
            for pid, p in lib_for_solver.items()
        }

    return lib_for_solver, rep_of


def _serialize_solutions(solutions, piece_lib, lib_for_solver, rep_of):
    """Convert solver output into JSON-serializable solution data."""
    serialized = []
    for sol in solutions:
        sdata = []
        for cand in sol:
            canon_id = cand.piece_id
            orig_id = rep_of.get(canon_id, canon_id)
            src_piece = piece_lib.get(orig_id) or lib_for_solver.get(canon_id)
            color = getattr(src_piece, 'color', None) or 'red'
            sdata.append({
                'id': orig_id,
                'color': color,
                'cells': cand.cells,
                'orientation': cand.orientation,
                'position': cand.position,
            })
        serialized.append(sdata)
    return serialized


# ── Routes ──────────────────────────────────────────────────────────────────

@solve_api.route('/api/solve', methods=['POST'])
def solve_puzzle():
    try:
        data = request.json
        params = _parse_solve_request(data)

        board = Board(params['width'], params['height'])
        if params['obstacles']:
            board.add_obstacles(params['obstacles'])

        piece_lib = _build_piece_library(
            params['library_id'],
            params['selected_pieces'],
            params['allow_reflections'],
            params['allow_rotations'],
        )
        if not piece_lib:
            return jsonify({'success': False, 'message': 'No valid pieces selected for solving the puzzle.'})

        lib_for_solver, rep_of = _prepare_solver_library(
            piece_lib,
            params['selected_pieces'],
            params['dedupe_equivalent'],
            params['library_id'],
            params['allow_reflections'],
            params['allow_rotations'],
        )

        puzzle = TilingPuzzle(board, lib_for_solver)
        solver = PySatSolver()
        solutions = solver.solve(puzzle, max_solutions=params['max_solutions'], threads=params['threads'])

        if not solutions:
            return jsonify({'success': False, 'message': 'No solution found for the given configuration.'})
        if isinstance(params['max_solutions'], int) and params['max_solutions'] == 1:
            solutions = [solutions]

        serialized = _serialize_solutions(solutions, piece_lib, lib_for_solver, rep_of)

        response_payload = {
            'success': True,
            'solutions': serialized,
            'board': {'width': params['width'], 'height': params['height'], 'obstacles': params['obstacles']},
        }

        if params['persist']:
            try:
                libraries = load_libraries_index()
                lib = next((l for l in libraries if l.get('id') == params['library_id']), None)
                library_name = lib.get('name') if lib else params['library_id']
                rec = add_solution_record(
                    params['save_name'],
                    {'width': params['width'], 'height': params['height'], 'obstacles': params['obstacles']},
                    params['library_id'],
                    library_name,
                    params['selected_pieces'],
                    serialized,
                )
                response_payload['saved'] = True
                response_payload['saved_id'] = rec.get('id')
            except Exception as e:
                logger.exception("Failed to persist solution")
                response_payload['saved'] = False
                response_payload['save_error'] = str(e)

        return jsonify(response_payload)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        logger.exception("Unexpected error in solve_puzzle")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@solve_api.route('/api/solutions', methods=['GET'])
def list_solutions():
    try:
        return jsonify({'success': True, 'solutions': list_solution_summaries()})
    except Exception as e:
        logger.exception("Failed to list solutions")
        return jsonify({'success': False, 'message': str(e)}), 500


@solve_api.route('/api/solutions/<solution_id>', methods=['GET'])
def get_solution(solution_id):
    try:
        rec = find_solution_by_id(solution_id)
        if not rec:
            return jsonify({'success': False, 'message': f'Solution {solution_id} not found'}), 404
        return jsonify({'success': True, 'record': rec})
    except Exception as e:
        logger.exception("Failed to get solution %s", solution_id)
        return jsonify({'success': False, 'message': str(e)}), 500
