"""Initialise the database and load seed rules.

Usage (from the backend/ folder):
    python -m app.seed            # create tables, insert missing rules
    python -m app.seed --update   # also update existing rules from data/seed/rules.json
    python -m app.seed --reset    # drop everything first, then re-create and seed

Also creates the default lead and trainee logins (only if there are no users yet)
and adds any PDFs placed in data/seed/documents/ to Errors & solutions.
"""
import argparse

from app.database import DATABASE_URL, Base, SessionLocal, engine, init_db
from app.services.auth_service import ensure_default_users
from app.services.document_service import seed_documents
from app.services.seed_service import seed_examples, seed_rules


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
        examples_added = seed_examples(db)
        users_created = ensure_default_users(db)
        documents_added = seed_documents(db)
    print(f"Database: {DATABASE_URL}")
    print(
        f"Rules inserted: {result.inserted}, updated: {result.updated}, "
        f"unchanged: {result.unchanged}"
    )
    print(f"Examples added: {examples_added}")
    print(f"Errors & solutions PDFs added from data/seed/documents/: {documents_added}")
    if users_created:
        print(f"Default accounts created: {', '.join(users_created)} (see backend/.env.example).")
        print("Change their passwords with: python -m app.users set-password <username>")


if __name__ == "__main__":
    main()
