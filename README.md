A tilling puzzle (Polyominoes) solver. As far as I know, there currently isn't any such solver available that is easily accessible, easy to use, efficient, decent UI, and allow the addition of custom pieces. This solver solves all the mentioned problems.

It contains a Flask-web UI, easy to use and intuitive. It converts the tilling problem into a SAT problem and uses a SAT solver to solve it. 

### To install:

```
pip install -r requirements.txt
```

### To run:

From the project root:

```
python server/run.py
```

This starts the Flask UI and will automatically migrate any existing SQLite database to JSON on first run.

### Storage (JSON, no .db)

- The app now uses a JSON file instead of SQLite.
- Location: `instance/polyomino.json`.
- On startup, if `polyomino.json` is missing but a `polyomino.db` exists (either at `frontend/instance/polyomino.db` or `instance/polyomino.db`), the app exports all libraries and pieces into the JSON file automatically.
- You can also run the migration manually:

```
python server/migrate_db_to_json.py
```

- JSON schema overview:
  - `libraries`: list of `{ id, name, editable, created_at, updated_at }`
  - `pieces`: list of `{ library_id, name, color, cells }` where `cells` is `[[row, col], ...]`

### Multiple solutions

- In the UI, set "Number of solutions" to search for more than one solution (can be slower).
- The backend accepts `max_solutions` in `/api/solve` requests and returns an array `solutions`.

### Persisting solutions

- Check "Save solutions" and optionally enter a name before solving.
- The server persists the results into `instance/polyomino.json` under `solutions`.
- API: include `persist: true` and optional `save_name` in `/api/solve` body. Response includes `saved` and `saved_id`.

### Loading saved solutions

- In the UI, use the "Saved Solutions" dropdown and click "Load".
- API:
  - List: `GET /api/solutions` returns `{ success, solutions: [{ id, name, created_at, num_solutions, library_id, board: { width, height } }] }`.
  - Get: `GET /api/solutions/<id>` returns `{ success, record }` where `record.solutions` is the same format as the solve response.

![image](https://github.com/user-attachments/assets/1b48327d-5a3b-4f09-998e-ed799b940d92)

Screenshot shows a solution that covers the entire board of the game Patchwork
