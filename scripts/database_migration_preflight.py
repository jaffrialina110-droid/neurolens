"""Read-only preflight inspection for NeuroLens SQLite databases.

This module NEVER migrates, modifies, creates, or deletes a database.
It reports schema metadata and row counts only; it never reads row contents.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


def inspect_database(path: str | Path) -> dict[str, Any]:
    db_path = Path(path).expanduser()
    result: dict[str, Any] = {
        "path": str(db_path),
        "exists": db_path.is_file(),
        "integrity": "not_checked",
        "tables": [],
        "errors": [],
    }
    if not result["exists"]:
        return result

    # mode=ro prevents accidental writes during inspection.
    uri = db_path.resolve().as_uri() + "?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            integrity_rows = connection.execute("PRAGMA integrity_check").fetchall()
            result["integrity"] = (
                "ok" if len(integrity_rows) == 1
                and integrity_rows[0][0] == "ok"
                else [row[0] for row in integrity_rows]
            )
            fk_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
            result["foreign_key_violations"] = len(fk_errors)

            table_names = connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
                "ORDER BY name"
            ).fetchall()

            for row in table_names:
                table = row["name"]
                # Table names originate from sqlite_master, not user input.
                columns = connection.execute(
                    f'PRAGMA table_info("{table.replace(chr(34), chr(34) * 2)}")'
                ).fetchall()
                count = connection.execute(
                    f'SELECT COUNT(*) FROM "{table.replace(chr(34), chr(34) * 2)}"'
                ).fetchone()[0]
                result["tables"].append({
                    "name": table,
                    "row_count": count,
                    "columns": [
                        {
                            "name": column["name"],
                            "type": column["type"],
                            "not_null": bool(column["notnull"]),
                            "primary_key": bool(column["pk"]),
                        }
                        for column in columns
                    ],
                })
        finally:
            connection.close()
    except (sqlite3.Error, OSError) as exc:
        result["errors"].append(f"{type(exc).__name__}: {exc}")
    return result


def build_comparison(reports: list[dict[str, Any]]) -> dict[str, Any]:
    by_table: dict[str, list[dict[str, Any]]] = {}
    for report in reports:
        for table in report.get("tables", []):
            by_table.setdefault(table["name"], []).append({
                "database": report["path"],
                "row_count": table["row_count"],
                "columns": [column["name"] for column in table["columns"]],
            })

    return {
        "shared_table_names": {
            name: entries for name, entries in by_table.items()
            if len(entries) > 1
        },
        "note": (
            "Matching table names do not imply compatible schemas or "
            "safe-to-merge records. No records were copied."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only NeuroLens SQLite migration preflight."
    )
    parser.add_argument(
        "databases", nargs="+",
        help="Existing SQLite database paths to inspect."
    )
    args = parser.parse_args()

    reports = [inspect_database(path) for path in args.databases]
    output = {
        "mode": "read_only_preflight",
        "databases": reports,
        "comparison": build_comparison(reports),
        "migration_performed": False,
    }
    print(json.dumps(output, indent=2))
    return 0 if all(not report["errors"] for report in reports) else 2


if __name__ == "__main__":
    raise SystemExit(main())
