"""Initialise the database and load seed rules.

Usage (from the backend/ folder):
    python -m app.seed            # create tables, insert missing rules
    python -m app.seed --update   # also update existing rules from data/seed/rules.json
    python -m app.seed --reset    # drop everything first, then re-create and seed
"""
import argparse

from app.database import DATABASE_URL, Base, SessionLocal, engine, init_db
from app.services.seed_service import seed_rules


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialise and seed the database.")
    parser.add_argument("--reset", action="store_true", help="drop all tables first")
    parser.add_argument(
        "--update", action="store_true", help="update existing rules to match the seed file"
    )
    args = parser.parse_args()

    if args.reset:
        import app.models  # noqa: F401

        Base.metadata.drop_all(bind=engine)
        print("Dropped all tables.")

    init_db()
    with SessionLocal() as db:
        result = seed_rules(db, update=args.update)
    print(f"Database: {DATABASE_URL}")
    print(
        f"Rules inserted: {result.inserted}, updated: {result.updated}, "
        f"unchanged: {result.unchanged}"
    )


if __name__ == "__main__":
    main()
