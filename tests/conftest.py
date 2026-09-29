import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.core.security import get_password_hash, RolePermissions
import backend.app.models
from backend.app.models.user import User
from backend.app.models.station import Station
from backend.app.models.reading import StationReading
from backend.app.models.fire import FireEvent
from backend.app.models.weather import WeatherSnapshot
from backend.app.models.alert import Alert

# Single shared in-memory SQLite engine with StaticPool
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(
    TEST_DB_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def db_lifecycle():
    """Create all tables and seed standard test baseline before each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        # Seed users
        admin_user = User(
            email="admin@vayu-net.org",
            hashed_password=get_password_hash("AdminPassword123!"),
            full_name="Administrator",
            role=RolePermissions.ADMIN,
            is_active=True,
        )
        citizen_user = User(
            email="citizen@vayu-net.org",
            hashed_password=get_password_hash("CitizenPassword123!"),
            full_name="Citizen User",
            role=RolePermissions.PUBLIC,
            is_active=True,
        )
        partner_user = User(
            email="partner@brics-climate.org",
            hashed_password=get_password_hash("PartnerPassword123!"),
            full_name="BRICS Partner Agency",
            role=RolePermissions.PARTNER_API_KEY,
            api_key="brics-partner-secret-key-001",
            is_active=True,
        )
        session.add(admin_user)
        session.add(citizen_user)
        session.add(partner_user)

        # Seed stations
        delhi_stn = Station(
            id="stn-delhi-001",
            external_id="openaq_delhi_hub",
            name="Delhi Reference Station",
            city="Delhi-NCR",
            state="Delhi",
            latitude=28.6139,
            longitude=77.2090,
            is_active=True,
            data_source="OPENAQ",
            is_stale=False,
            last_sync=datetime.now(timezone.utc),
        )
        session.add(delhi_stn)

        # Seed readings
        now = datetime.now(timezone.utc)
        r_measured = StationReading(
            station_id="stn-delhi-001",
            timestamp=now,
            parameter="pm25",
            value=145.0,
            unit="ug/m3",
            aqi_value=320,
            aqi_category="Very Poor",
            data_origin="MEASURED",
        )
        r_modelled = StationReading(
            station_id="stn-delhi-001",
            timestamp=now - timedelta(hours=1),
            parameter="pm25",
            value=130.0,
            unit="ug/m3",
            aqi_value=305,
            aqi_category="Very Poor",
            data_origin="MODELLED",
        )
        session.add(r_measured)
        session.add(r_modelled)

        # Seed fire event
        fire = FireEvent(
            external_id="viirs_30.9_75.8_test",
            latitude=30.901,
            longitude=75.857,
            frp_mw=125.4,
            brightness_temp_k=342.5,
            acquisition_time=now - timedelta(hours=2),
            confidence="high",
            satellite="VIIRS_SNPP",
            day_night="D",
        )
        session.add(fire)

        # Seed weather
        weather = WeatherSnapshot(
            city="Delhi-NCR",
            latitude=28.6139,
            longitude=77.2090,
            timestamp=now,
            temperature_2m_c=28.5,
            relative_humidity_2m_pct=62.0,
            wind_speed_10m_kmh=12.5,
            wind_direction_10m_deg=315.0,
            boundary_layer_height_m=420.0,
        )
        session.add(weather)

        # Seed alert
        alert = Alert(
            id="alert-001",
            cap_identifier="urn:oid:2.49.0.0.356.vayu.test.001",
            corridor_id="indo-gangetic-main",
            city="Delhi-NCR",
            severity="SEVERE",
            title_en="Severe Smog Alert",
            title_hi="गंभीर धुंध चेतावनी",
            description_en="High PM2.5 levels detected along the corridor.",
            description_hi="गलियारे में उच्च पीएम 2.5 स्तर दर्ज किया गया।",
            evidence={"pm25": 145.0, "frp": 125.4},
            rule_trigger="FORECAST_SPIKE",
            status="NEW",
        )
        session.add(alert)
        await session.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
