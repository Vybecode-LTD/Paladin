"""Seed the first admin user. Run once after DB is up:
    python -m seed
Reads SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD from env, with dev defaults.
"""
import asyncio
import os
from sqlalchemy import select
from app.core.database import async_session, engine
from app.models import Base
from app.models.user import User, UserRole
from app.core.security import hash_password


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    email = os.getenv("SEED_ADMIN_EMAIL", "admin@ashfordbriggs.com")
    password = os.getenv("SEED_ADMIN_PASSWORD", "ChangeMe123!")

    async with async_session() as db:
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            print(f"Admin {email} already exists — skipping.")
            return
        admin = User(
            email=email,
            hashed_password=hash_password(password),
            full_name="Site Admin",
            role=UserRole.admin,
        )
        db.add(admin)
        await db.commit()
        print(f"Created admin: {email}")
        print("IMPORTANT: change this password after first login.")


if __name__ == "__main__":
    asyncio.run(main())
