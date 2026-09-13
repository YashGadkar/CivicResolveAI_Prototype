from argon2 import PasswordHasher
from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import User

password_hasher = PasswordHasher()

DEMO_EMPLOYEES = [
    {
        "name": "Rohan Sharma",
        "email": "rohan.sharma@civicresolve.gov.in",
        "role": "OFFICER",
        "department": "Roads & Public Works Department",
    },
    {
        "name": "Priya Deshmukh",
        "email": "priya.water@civicresolve.gov.in",
        "role": "OFFICER",
        "department": "Water Supply Department",
    },
    {
        "name": "Vikram Patil",
        "email": "patil.electrical@civicresolve.gov.in",
        "role": "OFFICER",
        "department": "Electrical Services Department",
    },
    {
        "name": "Ananya Joshi",
        "email": "ananya.sanitation@civicresolve.gov.in",
        "role": "OFFICER",
        "department": "Sanitation Department",
    },
    {
        "name": "Rajesh Kulkarni",
        "email": "admin@civicresolve.gov.in",
        "role": "ADMIN",
        "department": "Municipal Governance Administration",
    },
    {
        "name": "Demo Officer",
        "email": "officer@civicresolve.local",
        "role": "OFFICER",
        "department": "Civic Operations",
    },
    {
        "name": "Demo Admin",
        "email": "admin@civicresolve.local",
        "role": "ADMIN",
        "department": "Governance & Analytics",
    },
]

DEFAULT_PASSWORD = "Password@1234"


def seed_employees() -> None:
    with SessionLocal() as db:
        hashed = password_hasher.hash(DEFAULT_PASSWORD)
        created_count = 0
        updated_count = 0

        for emp in DEMO_EMPLOYEES:
            email = emp["email"].strip().lower()
            user = db.scalar(select(User).where(func.lower(User.email) == email))
            if user:
                user.name = emp["name"]
                user.role = emp["role"]
                user.password_hash = hashed
                updated_count += 1
            else:
                user = User(
                    name=emp["name"],
                    email=email,
                    password_hash=hashed,
                    role=emp["role"],
                )
                db.add(user)
                created_count += 1

        db.commit()
        print(f"Successfully seeded demo employees! Created: {created_count}, Updated: {updated_count}")
        print(f"Universal demo password: {DEFAULT_PASSWORD}")


if __name__ == "__main__":
    seed_employees()
