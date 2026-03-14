from flask import Blueprint, request, jsonify
import datetime

from backend.board import Board
from backend.TilingPuzzle import TilingPuzzle
from backend.pieceLibrary import test_piece_library
from server.services.solver_service import JSONPieceAdapter, group_equivalent_pieces
from server.json_storage import (
    read_library_pieces,
    add_solution_record,
    list_solution_summaries,
    find_solution_by_id,
    load_libraries_index
)

solve_api = Blueprint('solve_api', __name__)

def _list_libraries_index():
    return load_libraries_index()

def _list_pieces_for_library(library_id):
    return read_library_pieces(library_id)

@solve_api.route('/api/solve', methods=['POST'])
def solve_puzzle():
    try:
        data = request.json
        width = data.get('width', 4)
        height = data.get('height', 4)
        obstacles = data.get('obstacles', [])
        selected_pieces = data.get('pieces', [])
        library_id = data.get('library_id', 'builtin')
        
        try:
            max_solutions = int(data.get('max_solutions', 1))
        except ValueError:
            max_solutions = 1
            
        persist = bool(data.get('persist', False))
        save_name = str(data.get('save_name', '')).strip() or f"Solution {datetime.datetime.utcnow().isoformat()}"
        dedupe_equivalent = bool(data.get('dedupe_equivalent', True))
        
        allow_reflections = data.get('allow_reflections', True)
        allow_rotations = data.get('allow_rotations', True)

        obstacle_positions = [(i, j) for i, j in obstacles]

        board = Board(width, height)
        if obstacle_positions:
            board.addObstacles(obstacle_positions)

        piece_lib = {}
        if library_id == 'builtin':
            piece_lib = test_piece_library if not selected_pieces else {k: test_piece_library[k] for k in selected_pieces if k in test_piece_library}
        else:
            pieces = _list_pieces_for_library(library_id)
            pdict = {p['name']: JSONPieceAdapter({**p, 'allow_reflections': allow_reflections, 'allow_rotations': allow_rotations}) for p in pieces}
            for pid in selected_pieces:
                if pid in pdict:
                    piece_lib[pid] = pdict[pid]

        if not piece_lib:
            return jsonify({'success': False, 'message': 'No valid pieces selected for solving the puzzle.'})

        # Optionally dedupe equivalent shapes
        lib_for_solver = piece_lib
        canonical_of = {pid: pid for pid in piece_lib.keys()}
        if dedupe_equivalent:
            lib_for_solver, canonical_of = group_equivalent_pieces(piece_lib)

        rep_of = {}
        for pid in selected_pieces:
            canon = canonical_of.get(pid, pid)
            if canon not in rep_of:
                rep_of[canon] = pid
        for pid, canon in canonical_of.items():
            rep_of.setdefault(canon, pid)

        if library_id == 'builtin' and (allow_reflections is False or allow_rotations is False):
            lib_for_solver = {
                pid: JSONPieceAdapter({
                    'name': pid,
                    'color': getattr(p, 'color', None),
                    'cells': [[i, j] for (i, j) in (p.get_offsets() if hasattr(p, 'get_offsets') else [])],
                    'allow_reflections': allow_reflections,
                    'allow_rotations': allow_rotations
                })
                for pid, p in lib_for_solver.items()
            }
            
        puzzle = TilingPuzzle(board, lib_for_solver)
        
        try:
            threads = int(data.get('threads')) if data.get('threads') is not None else None
        except ValueError:
            threads = None
            
        solutions = puzzle.solve(max_solutions=max_solutions, threads=threads)

        if not solutions:
            return jsonify({'success': False, 'message': 'No solution found for the given configuration.'})
        if isinstance(max_solutions, int) and max_solutions == 1:
            solutions = [solutions]

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

@solve_api.route('/api/solutions', methods=['GET'])
def list_solutions():
    try:
        return jsonify({'success': True, 'solutions': list_solution_summaries()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@solve_api.route('/api/solutions/<solution_id>', methods=['GET'])
def get_solution(solution_id):
    try:
        rec = find_solution_by_id(solution_id)
        if not rec:
            return jsonify({'success': False, 'message': f'Solution {solution_id} not found'}), 404
        return jsonify({'success': True, 'record': rec})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
