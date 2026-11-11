"""Administrator commands, run from a trusted environment with database access."""
import argparse

from sqlalchemy import update

from .main import engine, fetch, schema, users


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email")
    parser.add_argument("role", choices=["ADMIN", "SUPPORT_MANAGER", "SUPPORT_AGENT", "AUDITOR"])
    args = parser.parse_args()
    email = args.email.strip().lower()
    schema.create_all(engine)
    user = fetch(users, email)
    if user is None:
        parser.error("Register the account before assigning a role.")
    with engine.begin() as connection:
        connection.execute(update(users).where(users.c.id == email).values(payload={**user, "role": args.role}))
    print(f"Assigned {args.role} to {email}.")


if __name__ == "__main__":
    main()
