"""Manage login accounts from the command line.

Usage (from the backend/ folder, with the venv active):
    python -m app.users list
    python -m app.users create <username> --role lead|trainee [--name "Full Name"]
    python -m app.users set-password <username>
    python -m app.users set-role <username> lead|trainee
    python -m app.users disable <username>
    python -m app.users enable <username>

Passwords are asked for interactively (not shown, not saved in shell history).
"""
import argparse
import getpass
import sys

from app.database import SessionLocal, init_db
from app.models import ROLES
from app.services import auth_service


def _ask_password() -> str:
    first = getpass.getpass("New password: ")
    if first != getpass.getpass("Repeat password: "):
        sys.exit("Passwords do not match.")
    return first


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage Redline login accounts.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    create = sub.add_parser("create")
    create.add_argument("username")
    create.add_argument("--role", choices=ROLES, required=True)
    create.add_argument("--name", default=None)
    for name in ("set-password", "disable", "enable"):
        sub.add_parser(name).add_argument("username")
    role = sub.add_parser("set-role")
    role.add_argument("username")
    role.add_argument("role", choices=ROLES)
    args = parser.parse_args()

    init_db()
    with SessionLocal() as db:
        if args.command == "list":
            from sqlalchemy import select

            from app.models import User

            for user in db.scalars(select(User).order_by(User.role, User.username)):
                state = "" if user.is_active else "  (disabled)"
                print(f"{user.username:<20} {user.role:<8} {user.display_name}{state}")
            return

        if args.command == "create":
            try:
                auth_service.create_user(db, args.username, _ask_password(), args.role, args.name)
            except ValueError as error:
                sys.exit(str(error))
            print(f"Created {args.role} '{args.username}'.")
            return

        user = auth_service.get_user_by_username(db, args.username)
        if user is None:
            sys.exit(f"No user called '{args.username}'.")
        if args.command == "set-password":
            try:
                auth_service.set_password(db, user, _ask_password())
            except ValueError as error:
                sys.exit(str(error))
            print("Password changed.")
        elif args.command == "set-role":
            user.role = args.role
            db.commit()
            print(f"'{user.username}' is now a {args.role}. They must sign in again.")
        else:
            user.is_active = args.command == "enable"
            db.commit()
            print(f"'{user.username}' {'enabled' if user.is_active else 'disabled'}.")


if __name__ == "__main__":
    main()
