import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, get_db
from backend.main import app
from backend.models import User, Store, Product, Event
from backend.auth import hash_password, create_access_token

# Use SQLite in-memory for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed test users
    admin = User(
        username="test_admin",
        hashed_password=hash_password("admin123"),
        full_name="Test Admin",
        role="admin",
        city="Chennai"
    )
    planner = User(
        username="test_planner",
        hashed_password=hash_password("planner123"),
        full_name="Test Planner",
        role="planner",
        city="Chennai"
    )
    viewer = User(
        username="test_viewer",
        hashed_password=hash_password("viewer123"),
        full_name="Test Viewer",
        role="viewer",
        city="Chennai"
    )
    db.add_all([admin, planner, viewer])

    # Seed test store
    store = Store(
        store_code="TEST-ST-01",
        store_name="Test Chennai Store",
        city="Chennai",
        latitude=13.0827,
        longitude=80.2707,
        store_type="Flagship",
        size_sqft=6000
    )
    db.add(store)

    # Seed test product
    product = Product(
        sku="TEST-TRAD-001",
        category="Traditional Wear",
        name="Test Silk Saree",
        unit_cost=600.0,
        retail_price=1800.0
    )
    db.add(product)

    # Seed test event
    event = Event(
        name="Test Grand Festival",
        description="Test cultural festival",
        event_type="Festival",
        start_date="2026-09-20",
        end_date="2026-09-25",
        latitude=13.0850,
        longitude=80.2750,
        location_name="Test Grounds",
        city="Chennai",
        expected_attendance=15000,
        status="active",
        impact_radius_km=15.0
    )
    db.add(event)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(setup_test_db):
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def planner_auth_header(db_session):
    user = db_session.query(User).filter(User.username == "test_planner").first()
    token = create_access_token(user.id, user.username, user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_auth_header(db_session):
    user = db_session.query(User).filter(User.username == "test_viewer").first()
    token = create_access_token(user.id, user.username, user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_header(db_session):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    token = create_access_token(user.id, user.username, user.role)
    return {"Authorization": f"Bearer {token}"}
