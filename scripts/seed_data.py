import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import select
from backend.app.core.database import AsyncSessionLocal, async_engine, Base
from backend.app.core.security import get_password_hash, RolePermissions
from backend.app.core.config import settings
from backend.app.models.user import User
from backend.app.models.station import Station
from backend.app.models.audit import AuditLog


async def seed():
    print("=" * 60)
    print("  VAYU-NET: Initializing Database & Seeding Core Accounts")
    print("=" * 60)

    # 1. Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] Database tables verified and created.")

    async with AsyncSessionLocal() as session:
        # 2. Seed Default Accounts
        users_to_seed = [
            {
                "email": "admin@vayu-net.org",
                "password": "AdminPassword123!",
                "full_name": "System Administrator",
                "role": RolePermissions.ADMIN,
                "api_key": None
            },
            {
                "email": "authority@vayu-net.org",
                "password": "AuthorityPassword123!",
                "full_name": "Air Quality Emergency Authority",
                "role": RolePermissions.AUTHORITY,
                "api_key": None
            },
            {
                "email": "analyst@vayu-net.org",
                "password": "AnalystPassword123!",
                "full_name": "Atmospheric Modeler & Analyst",
                "role": RolePermissions.ANALYST,
                "api_key": None
            },
            {
                "email": "partner@brics-climate.org",
                "password": "PartnerPassword123!",
                "full_name": "BRICS Air Quality Research Node",
                "role": RolePermissions.PARTNER_API_KEY,
                "api_key": "vayu_partner_test_key_brics_2026"
            }
        ]

        for u in users_to_seed:
            stmt = select(User).where(User.email == u["email"])
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if not existing:
                new_user = User(
                    email=u["email"],
                    hashed_password=get_password_hash(u["password"]),
                    full_name=u["full_name"],
                    role=u["role"],
                    api_key=u["api_key"],
                    is_active=True
                )
                session.add(new_user)
                print(f"[OK] Created user: {u['email']} (Role: {u['role']})")
            else:
                print(f"[*] User already exists: {u['email']}")

        # 3. Seed Corridor Stations
        corridors_cfg = settings.get_corridors_config()
        station_count = 0
        for c in corridors_cfg.get("corridors", []):
            for node in c.get("nodes", []):
                ext_id = f"stn_{node['city'].lower().replace(' ', '_').replace('-', '_')}"
                stmt = select(Station).where(Station.external_id == ext_id)
                stn_exists = (await session.execute(stmt)).scalar_one_or_none()
                if not stn_exists:
                    new_stn = Station(
                        external_id=ext_id,
                        name=f"{node['city']} Central Reference Station",
                        city=node["city"],
                        state=node["state"],
                        latitude=node["lat"],
                        longitude=node["lon"],
                        elevation_m=node.get("elevation_m", 200.0),
                        is_active=True,
                        data_source="OPENAQ",
                        is_stale=False
                    )
                    session.add(new_stn)
                    station_count += 1

        print(f"[OK] Seeded {station_count} reference monitor stations from corridors config.")

        # 4. Add system bootstrap audit record
        audit = AuditLog(
            action="SYSTEM_BOOTSTRAP",
            resource_type="system",
            resource_id="vayu-net-core",
            user_email="system@vayu-net.org",
            user_role="system",
            details={"message": "Initial database seed completed successfully."}
        )
        session.add(audit)
        await session.commit()

    print("\n" + "=" * 60)
    print("  SEEDING COMPLETE! Credentials for testing:")
    print("  * Admin:     admin@vayu-net.org     / AdminPassword123!")
    print("  * Authority: authority@vayu-net.org / AuthorityPassword123!")
    print("  * Analyst:   analyst@vayu-net.org   / AnalystPassword123!")
    print("  * Partner API Key: vayu_partner_test_key_brics_2026")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
