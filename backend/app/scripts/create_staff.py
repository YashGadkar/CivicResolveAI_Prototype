import argparse
import getpass
import re

from app.database import SessionLocal
from app.schemas import validate_password_strength
from app.services.auth import EmailAlreadyRegistered, create_user

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a CivicResolve employee account.")
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--role", choices=["OFFICER", "ADMIN"], default="OFFICER")
    parser.add_argument("--password", help="Omit to enter the password securely.")
    args = parser.parse_args()

    email = args.email.strip().lower()
    if not EMAIL_RE.fullmatch(email):
        raise SystemExit("Enter a valid employee email address.")

    password = args.password or getpass.getpass("Password: ")
    try:
        validate_password_strength(password)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    with SessionLocal() as db:
        try:
            user = create_user(db, args.name, email, password, role=args.role)
        except EmailAlreadyRegistered as exc:
            raise SystemExit(str(exc)) from exc

    print(f"Created {user.role} account for {user.email}.")


if __name__ == "__main__":
    main()
