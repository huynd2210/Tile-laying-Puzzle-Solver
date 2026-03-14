import json
import logging
import os
import datetime
import uuid
from contextlib import contextmanager
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def _paths() -> Dict[str, str]:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    instance_dir = os.environ.get('INSTANCE_DIR') or os.path.join(base_dir, 'instance')
    libraries_index = os.path.join(instance_dir, 'libraries.json')
    libraries_dir = os.path.join(instance_dir, 'libraries')
    solutions_path = os.path.join(instance_dir, 'solutions.json')  # legacy monolith
    solutions_dir = os.path.join(instance_dir, 'solutions')
    monolith_path = os.path.join(instance_dir, 'polyomino.json')
    return {
        'instance': instance_dir,
        'libraries_index': libraries_index,
        'libraries_dir': libraries_dir,
        'solutions': solutions_path,
        'solutions_dir': solutions_dir,
        'monolith': monolith_path,
    }


def ensure_dirs() -> None:
    ps = _paths()
    for p in [ps['instance'], ps['libraries_dir'], ps['solutions_dir']]:
        if not os.path.exists(p):
            os.makedirs(p, exist_ok=True)


def current_iso_time() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ── Cross-platform file locking ─────────────────────────────────────────────

@contextmanager
def _file_lock(filepath: str):
    """
    A simple cross-platform advisory file lock.

    Uses msvcrt on Windows, fcntl on POSIX.
    """
    lockpath = filepath + '.lock'
    os.makedirs(os.path.dirname(lockpath) or '.', exist_ok=True)
    lockfile = open(lockpath, 'w')
    try:
        try:
            import msvcrt
            msvcrt.locking(lockfile.fileno(), msvcrt.LK_LOCK, 1)
        except ImportError:
            import fcntl
            fcntl.flock(lockfile, fcntl.LOCK_EX)
        yield
    finally:
        try:
            import msvcrt
            msvcrt.locking(lockfile.fileno(), msvcrt.LK_UNLCK, 1)
        except ImportError:
            import fcntl
            fcntl.flock(lockfile, fcntl.LOCK_UN)
        lockfile.close()


# ── Core Data I/O Helpers ───────────────────────────────────────────────────

def _load_json(filepath: str, default: Any = None) -> Any:
    """Safely load JSON from a file under a lock, returning default on failure."""
    if not os.path.exists(filepath):
        return default
    try:
        with _file_lock(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load JSON from %s: %s", filepath, exc)
        return default


def _save_json(filepath: str, data: Any) -> bool:
    """Safely save JSON to a file under a lock."""
    ensure_dirs()
    try:
        with _file_lock(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except OSError as exc:
        logger.warning("Failed to save JSON to %s: %s", filepath, exc)
        return False


# ── Libraries index ─────────────────────────────────────────────────────────

def load_libraries_index() -> List[Dict[str, Any]]:
    ensure_dirs()
    data = _load_json(_paths()['libraries_index'], default=[])
    return data if isinstance(data, list) else []


def save_libraries_index(libraries: List[Dict[str, Any]]) -> None:
    _save_json(_paths()['libraries_index'], libraries)


# ── Per-library pieces ──────────────────────────────────────────────────────

def _library_file(library_id: str) -> str:
    return os.path.join(_paths()['libraries_dir'], f'{library_id}.json')


def remove_library_file(library_id: str) -> None:
    try:
        fp = _library_file(library_id)
        if os.path.exists(fp):
            os.remove(fp)
    except OSError as exc:
        logger.warning("Failed to remove library file for %s: %s", library_id, exc)


def read_library_pieces(library_id: str) -> List[Dict[str, Any]]:
    ensure_dirs()
    data = _load_json(_library_file(library_id), default=[])
    if isinstance(data, dict) and 'pieces' in data:
        return data.get('pieces') or []
    return data if isinstance(data, list) else []


def write_library_pieces(library_id: str, pieces: List[Dict[str, Any]]) -> None:
    _save_json(_library_file(library_id), {'pieces': pieces})


# ── Solutions store ─────────────────────────────────────────────────────────

def _solution_file_path(solution_id: str) -> str:
    return os.path.join(_paths()['solutions_dir'], f"{solution_id}.json")


def _iter_solution_files() -> List[str]:
    ensure_dirs()
    sdir = _paths()['solutions_dir']
    if not os.path.exists(sdir):
        return []
    return [os.path.join(sdir, fn) for fn in os.listdir(sdir) if fn.endswith('.json')]


def _get_library_name(library_id: str) -> str:
    for lib in load_libraries_index():
        if lib.get('id') == library_id:
            return lib.get('name') or library_id
    return library_id


def _read_legacy_solutions() -> List[Dict[str, Any]]:
    """Helper to read the legacy monolith solutions file if it exists."""
    legacy = _paths()['solutions']
    if not os.path.exists(legacy):
        return []
    try:
        with open(legacy, 'r', encoding='utf-8') as f:
            arr = json.load(f)
        return arr if isinstance(arr, list) else []
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read legacy solutions: %s", exc)
        return []


def add_solution_record(name: str, board: Dict[str, Any], library_id: str, library_name: str, selected_pieces: List[str], solutions_payload: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    rec_id = str(uuid.uuid4())
    record = {
        'id': rec_id,
        'name': name,
        'created_at': current_iso_time(),
        'board': board,
        'library_id': library_id,
        'library': library_name or _get_library_name(library_id),
        'pieces': selected_pieces,
        'solutions': solutions_payload,
        'num_solutions': len(solutions_payload)
    }
    _save_json(_solution_file_path(rec_id), record)
    return record


def find_solution_by_id(solution_id: str) -> Dict[str, Any]:
    # Prefer per-file store
    rec = _load_json(_solution_file_path(solution_id))
    if rec:
        if 'library' not in rec:
            rec['library'] = _get_library_name(rec.get('library_id'))
        return rec
        
    # Legacy monolith fallback
    for r in _read_legacy_solutions():
        if r.get('id') == solution_id:
            if 'library' not in r:
                r['library'] = _get_library_name(r.get('library_id'))
            return r
    return None


def list_solution_summaries() -> List[Dict[str, Any]]:
    summaries = []
    
    def _extract_summary(rec: Dict[str, Any]) -> Dict[str, Any]:
        board = rec.get('board') or {}
        return {
            'id': rec.get('id'),
            'name': rec.get('name'),
            'created_at': rec.get('created_at'),
            'num_solutions': rec.get('num_solutions'),
            'library_id': rec.get('library_id'),
            'library': rec.get('library') or _get_library_name(rec.get('library_id')),
            'board': {'width': board.get('width'), 'height': board.get('height')}
        }

    files = _iter_solution_files()
    if files:
        for fp in files:
            rec = _load_json(fp)
            if rec:
                summaries.append(_extract_summary(rec))
        return summaries
        
    # Legacy monolith fallback
    for rec in _read_legacy_solutions():
        summaries.append(_extract_summary(rec))
    
    return summaries


# ── Migration from monolith polyomino.json ──────────────────────────────────

def migrate_from_monolith() -> bool:
    monolith = _paths()['monolith']
    if not os.path.exists(monolith):
        return False
        
    try:
        with open(monolith, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read monolith for migration: %s", exc)
        return False

    libraries = data.get('libraries', []) if isinstance(data, dict) else []
    pieces = data.get('pieces', []) if isinstance(data, dict) else []
    solutions = data.get('solutions', []) if isinstance(data, dict) else []

    save_libraries_index(libraries)
    
    # Group pieces by library and write files
    by_lib: Dict[str, List[Dict[str, Any]]] = {}
    for p in pieces:
        by_lib.setdefault(p.get('library_id'), []).append(p)
    for lid, plist in by_lib.items():
        write_library_pieces(lid, plist)
        
    # Save solutions per-file
    for rec in (solutions if isinstance(solutions, list) else []):
        sid = rec.get('id') or str(uuid.uuid4())
        rec['id'] = sid
        _save_json(_solution_file_path(sid), rec)
        
    # Backup monolith
    try:
        os.replace(monolith, monolith + '.bak')
    except OSError:
        pass
    return True


def ensure_storage_initialized() -> None:
    ensure_dirs()
    if os.path.exists(_paths()['libraries_index']):
        # Also migrate legacy solutions.json to per-file if present
        legacy = _paths()['solutions']
        if os.path.exists(legacy) and not _iter_solution_files():
            for rec in _read_legacy_solutions():
                sid = rec.get('id') or str(uuid.uuid4())
                rec['id'] = sid
                _save_json(_solution_file_path(sid), rec)
            try:
                os.replace(legacy, legacy + '.bak')
            except OSError:
                pass
        return
        
    if migrate_from_monolith():
        return
        
    save_libraries_index([])
