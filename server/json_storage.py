import json
import os
import datetime
import uuid
from typing import Dict, Any, List


def _get_default_json_path() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    instance_dir = os.path.join(base_dir, 'instance')
    return os.path.join(instance_dir, 'polyomino.json')


def ensure_instance_dir(path: str) -> None:
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


def load_all(json_path: str = None) -> Dict[str, Any]:
    path = json_path or _get_default_json_path()
    if not os.path.exists(path):
        return {'libraries': [], 'pieces': [], 'solutions': []}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'libraries': [], 'pieces': [], 'solutions': []}


def save_all(data: Dict[str, Any], json_path: str = None) -> None:
    path = json_path or _get_default_json_path()
    ensure_instance_dir(path)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_libraries(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return data.get('libraries', [])


def set_libraries(data: Dict[str, Any], libraries: List[Dict[str, Any]]) -> None:
    data['libraries'] = libraries


def get_pieces(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return data.get('pieces', [])


def set_pieces(data: Dict[str, Any], pieces: List[Dict[str, Any]]) -> None:
    data['pieces'] = pieces


def current_iso_time() -> str:
    return datetime.datetime.utcnow().isoformat()


def get_solutions(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return data.get('solutions', [])


def set_solutions(data: Dict[str, Any], solutions: List[Dict[str, Any]]) -> None:
    data['solutions'] = solutions


def add_solution_record(data: Dict[str, Any], name: str, board: Dict[str, Any], library_id: str, selected_pieces: List[str], solutions_payload: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    record_id = str(uuid.uuid4())
    now = current_iso_time()
    record = {
        'id': record_id,
        'name': name,
        'created_at': now,
        'board': board,
        'library_id': library_id,
        'pieces': selected_pieces,
        'solutions': solutions_payload,
        'num_solutions': len(solutions_payload)
    }
    all_solutions = get_solutions(data)
    all_solutions.append(record)
    set_solutions(data, all_solutions)
    save_all(data)
    return record


def find_solution_by_id(data: Dict[str, Any], solution_id: str) -> Dict[str, Any]:
    for rec in get_solutions(data):
        if rec.get('id') == solution_id:
            return rec
    return None


def list_solution_summaries(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    summaries: List[Dict[str, Any]] = []
    for rec in get_solutions(data):
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


