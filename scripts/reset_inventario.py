from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db import CafeDB  # noqa: E402


def main() -> None:
    db = CafeDB()
    conn = db._conn  # uso interno controlado (script de mantenimiento)
    antes = conn.execute("SELECT COUNT(*) c FROM productos").fetchone()["c"]
    conn.execute("DELETE FROM productos")
    conn.execute("DELETE FROM sqlite_sequence WHERE name=?", ("productos",))
    conn.commit()
    despues = conn.execute("SELECT COUNT(*) c FROM productos").fetchone()["c"]
    db.close()
    print(f"productos antes={antes} despues={despues}")


if __name__ == "__main__":
    main()

