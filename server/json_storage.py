import json
import os
import datetime
import uuid
from typing import Dict, Any, List


def _paths() -> Dict[str, str]:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    instance_dir = os.path.join(base_dir, 'instance')
    libraries_index = os.path.join(instance_dir, 'libraries.json')
    libraries_dir = os.path.join(instance_dir, 'libraries')
    solutions_path = os.path.join(instance_dir, 'solutions.json')
    monolith_path = os.path.join(instance_dir, 'polyomino.json')
    return {
        'instance': instance_dir,
        'libraries_index': libraries_index,
        'libraries_dir': libraries_dir,
        'solutions': solutions_path,
        'monolith': monolith_path,
    }


def ensure_dirs() -> None:
    ps = _paths()
    for p in [ps['instance'], ps['libraries_dir']]:
        if not os.path.exists(p):
            os.makedirs(p)


def current_iso_time() -> str:
    return datetime.datetime.utcnow().isoformat()


# Libraries index
def load_libraries_index() -> List[Dict[str, Any]]:
    ensure_dirs()
    p = _paths()['libraries_index']
    if not os.path.exists(p):
        return []
    try:
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def save_libraries_index(libraries: List[Dict[str, Any]]) -> None:
    ensure_dirs()
    p = _paths()['libraries_index']
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(libraries, f, ensure_ascii=False, indent=2)


# Per-library pieces
def _library_file(library_id: str) -> str:
    return os.path.join(_paths()['libraries_dir'], f'{library_id}.json')


def read_library_pieces(library_id: str) -> List[Dict[str, Any]]:
    ensure_dirs()
    p = _library_file(library_id)
    if not os.path.exists(p):
        return []
    try:
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'pieces' in data:
                return data.get('pieces') or []
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []


def write_library_pieces(library_id: str, pieces: List[Dict[str, Any]]) -> None:
    ensure_dirs()
    p = _library_file(library_id)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump({'pieces': pieces}, f, ensure_ascii=False, indent=2)


# Solutions store
def load_solutions() -> List[Dict[str, Any]]:
    ensure_dirs()
    p = _paths()['solutions']
    if not os.path.exists(p):
        return []
    try:
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def save_solutions(solutions: List[Dict[str, Any]]) -> None:
    ensure_dirs()
    p = _paths()['solutions']
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(solutions, f, ensure_ascii=False, indent=2)


def add_solution_record(name: str, board: Dict[str, Any], library_id: str, selected_pieces: List[str], solutions_payload: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    rec_id = str(uuid.uuid4())
    now = current_iso_time()
    record = {
        'id': rec_id,
        'name': name,
        'created_at': now,
        'board': board,
        'library_id': library_id,
        'pieces': selected_pieces,
        'solutions': solutions_payload,
        'num_solutions': len(solutions_payload)
    }
    all_solutions = load_solutions()
    all_solutions.append(record)
    save_solutions(all_solutions)
    return record


def find_solution_by_id(solution_id: str) -> Dict[str, Any]:
    for rec in load_solutions():
        if rec.get('id') == solution_id:
            return rec
    return None


def list_solution_summaries() -> List[Dict[str, Any]]:
    summaries: List[Dict[str, Any]] = []
    for rec in load_solutions():
        board = rec.get('board') or {}
        summaries.append({
            'id': rec.get('id'),
            'name': rec.get('name'),
            'created_at': rec.get('created_at'),
            'num_solutions': rec.get('num_solutions'),
            'library_id': rec.get('library_id'),
            'board': {
                'width': board.get('width'),
                'height': board.get('height')
            }
        })
    return summaries


# Migration from monolith polyomino.json
def migrate_from_monolith() -> bool:
    ps = _paths()
    monolith = ps['monolith']
    if not os.path.exists(monolith):
        return False
    try:
        with open(monolith, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return False

    libraries = data.get('libraries', []) if isinstance(data, dict) else []
    pieces = data.get('pieces', []) if isinstance(data, dict) else []
    solutions = data.get('solutions', []) if isinstance(data, dict) else []

    ensure_dirs()
    # Write libraries index
    save_libraries_index(libraries)
    # Group pieces by library and write files
    by_lib: Dict[str, List[Dict[str, Any]]] = {}
    for p in pieces:
        lid = p.get('library_id')
        by_lib.setdefault(lid, []).append(p)
    for lid, plist in by_lib.items():
        write_library_pieces(lid, plist)
    # Save solutions
    save_solutions(solutions if isinstance(solutions, list) else [])
    # Backup monolith
    try:
        os.replace(monolith, monolith + '.bak')
    except Exception:
        pass
    return True


def ensure_storage_initialized() -> None:
    ensure_dirs()
    # If libraries index exists, assume initialized
    if os.path.exists(_paths()['libraries_index']):
        return
    # Try migrating from monolith
    if migrate_from_monolith():
        return
    # Otherwise create empty index and solutions
    save_libraries_index([])
    save_solutions([])



