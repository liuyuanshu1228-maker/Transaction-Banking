import argparse
import sqlite3
from contextlib import closing
from pathlib import Path

from src.data_generation import AS_OF, DEFAULT_SEED, generate

DEFAULT_DB = Path("data/synthetic/treasury.sqlite")
SCHEMA = """
CREATE TABLE accounts(id TEXT PRIMARY KEY, region TEXT NOT NULL, currency TEXT NOT NULL,
    opening_minor INTEGER NOT NULL, buffer_minor INTEGER NOT NULL);
CREATE TABLE fx(day TEXT, currency TEXT, usd_ppm INTEGER NOT NULL CHECK(usd_ppm > 0),
    PRIMARY KEY(day, currency));
CREATE TABLE payments(id INTEGER PRIMARY KEY, account TEXT REFERENCES accounts(id), instructed TEXT NOT NULL,
    currency TEXT NOT NULL, principal_minor INTEGER NOT NULL CHECK(principal_minor > 0),
    destination TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('settled','failed','pending')),
    outcome_day TEXT, CHECK((status = 'pending') = (outcome_day IS NULL)));
CREATE TABLE cashflows(id INTEGER PRIMARY KEY, account TEXT REFERENCES accounts(id), day TEXT NOT NULL,
    amount_minor INTEGER NOT NULL);
CREATE TABLE scheduled(id INTEGER PRIMARY KEY, account TEXT REFERENCES accounts(id), known_on TEXT NOT NULL,
    due_on TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('receipt','supplier')),
    currency TEXT NOT NULL, amount_minor INTEGER NOT NULL CHECK(amount_minor > 0));
CREATE TABLE transfers(id INTEGER PRIMARY KEY, day TEXT NOT NULL, source TEXT REFERENCES accounts(id),
    target TEXT REFERENCES accounts(id), amount_minor INTEGER NOT NULL CHECK(amount_minor > 0),
    CHECK(source <> target));
CREATE TABLE daily_balances(
    day TEXT, account TEXT REFERENCES accounts(id), currency TEXT NOT NULL,
    opening_minor INTEGER NOT NULL, inflow_minor INTEGER NOT NULL, outflow_minor INTEGER NOT NULL,
    fees_minor INTEGER NOT NULL, transfer_in_minor INTEGER NOT NULL, transfer_out_minor INTEGER NOT NULL,
    closing_minor INTEGER NOT NULL, buffer_minor INTEGER NOT NULL, closing_usd_minor INTEGER NOT NULL,
    PRIMARY KEY(day, account),
    CHECK(closing_minor = opening_minor + inflow_minor - outflow_minor - fees_minor
                          + transfer_in_minor - transfer_out_minor));
"""


def populate(connection, seed=DEFAULT_SEED):
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)
    with connection:
        for table, rows in generate(seed).items():
            placeholders = ", ".join("?" for _ in rows[0])
            connection.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)


def create_database(path=DEFAULT_DB, seed=DEFAULT_SEED):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb"):
        pass
    try:
        with closing(sqlite3.connect(path)) as connection:
            populate(connection, seed)
            from src.treasury import daily_balances

            rows = daily_balances(read_sources(connection), AS_OF)
            with connection:
                connection.executemany("""
                    INSERT INTO daily_balances VALUES (:day, :account, :currency, :opening_minor,
                    :inflow_minor, :outflow_minor, :fees_minor, :transfer_in_minor, :transfer_out_minor,
                    :closing_minor, :buffer_minor, :closing_usd_minor)
                """, rows)
    except Exception:
        path.unlink()
        raise
    return path


def read_sources(connection):
    connection.row_factory = sqlite3.Row
    return {table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY {order}")]
            for table, order in (("accounts", "id"), ("fx", "day, currency"), ("payments", "id"),
                                 ("cashflows", "id"), ("scheduled", "id"), ("transfers", "id"))}


def load(path=None, seed=DEFAULT_SEED):
    uri = ":memory:" if path is None else Path(path).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=path is not None)) as connection:
        if path is None:
            populate(connection, seed)
        return read_sources(connection)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a fresh synthetic treasury SQLite database.")
    parser.add_argument("--output", type=Path, default=DEFAULT_DB)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    print(create_database(args.output, args.seed))
