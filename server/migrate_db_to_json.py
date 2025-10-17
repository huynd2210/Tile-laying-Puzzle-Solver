import os
import json
import sqlite3
from typing import Dict, Any


def get_default_paths() -> Dict[str, str]:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    instance_dir = os.path.join(base_dir, 'instance')
    db_path = os.path.join(instance_dir, 'polyomino.db')
    json_path = os.path.join(instance_dir, 'polyomino.json')
    return {"db": db_path, "json": json_path}


def ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d)


def export_db_to_json(db_path: str, json_path: str) -> None:
    # Legacy exporter to monolith JSON for backward compatibility
    ensure_dir(json_path)
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, editable, created_at, updated_at FROM libraries")
        libraries = []
        for row in cur.fetchall():
            libraries.append({
                "id": row["id"],
                "name": row["name"],
                "editable": bool(row["editable"]) if row["editable"] is not None else True,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            })

        cur.execute("SELECT library_id, name, color, cells FROM pieces")
        pieces = []
        for row in cur.fetchall():
            cells_raw = row["cells"]
            cells = []
            if isinstance(cells_raw, str) and cells_raw:
                try:
                    cells = json.loads(cells_raw)
                except Exception:
                    cells = []
            elif isinstance(cells_raw, (bytes, bytearray)):
                try:
                    cells = json.loads(cells_raw.decode('utf-8'))
                except Exception:
                    cells = []
            pieces.append({
                "library_id": row["library_id"],
                "name": row["name"],
                "color": row["color"],
                "cells": cells,
            })

        out: Dict[str, Any] = {"libraries": libraries, "pieces": pieces, "solutions": []}
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"Export complete. Wrote JSON to: {json_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    paths = get_default_paths()
    export_db_to_json(paths["db"], paths["json"])


