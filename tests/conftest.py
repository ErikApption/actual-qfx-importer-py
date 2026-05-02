"""Shared pytest fixtures for qfx_importer tests."""
import json
import zipfile
from pathlib import Path

import pytest
from actual.database import Accounts, SQLModel
from actual.queries import get_or_create_clock
from sqlmodel import Session, create_engine

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# ---------------------------------------------------------------------------
# Fixture: QFX file bytes
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_qfx_bytes() -> bytes:
    """Return the raw bytes of the bundled sample QFX file."""
    return (FIXTURES_DIR / "sample.qfx").read_bytes()


# ---------------------------------------------------------------------------
# Fixture: minimal Actual Budget SQLite engine + session
# ---------------------------------------------------------------------------


@pytest.fixture()
def actual_engine(tmp_path):
    """Create a minimal Actual Budget SQLite engine in a temp directory.

    The database is initialised with all tables from the SQLModel metadata
    (same schema that actualpy uses) and a clock entry required for CRDT
    operations.
    """
    db_path = tmp_path / "db.sqlite"
    eng = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(eng)

    with Session(eng) as session:
        get_or_create_clock(session)
        session.commit()

    return eng


@pytest.fixture()
def actual_session(actual_engine):
    """Open a SQLModel session against the test Actual Budget database."""
    with Session(actual_engine) as session:
        yield session


# ---------------------------------------------------------------------------
# Fixture: test account
# ---------------------------------------------------------------------------

# The account_id used by the sample QFX fixture (ACCTID field)
SAMPLE_QFX_ACCOUNT_ID = "123456789"


@pytest.fixture()
def test_account(actual_session) -> Accounts:
    """Create a single test account in the Actual Budget database.

    The account name matches the ACCTID from ``sample.qfx`` so that the
    full end-to-end import path can be exercised.
    """
    acct = Accounts(
        id="test-checking-001",
        name=SAMPLE_QFX_ACCOUNT_ID,
        offbudget=0,
        closed=0,
    )
    actual_session.add(acct)
    actual_session.commit()
    actual_session.refresh(acct)
    return acct


# ---------------------------------------------------------------------------
# Fixture: minimal .actual zip file (Actual Budget backup format)
# ---------------------------------------------------------------------------


@pytest.fixture()
def actual_zip_path(actual_engine, tmp_path) -> Path:
    """Create a minimal ``.actual`` (zip) file that can be loaded via
    ``Actual.import_zip``.

    The zip contains:
    - ``db.sqlite`` – the test Actual Budget database (with schema + clock)
    - ``metadata.json`` – minimal metadata required by actualpy

    A test checking account matching the sample QFX account id is pre-created
    inside the database so that import tests can run end-to-end.
    """
    # Add the test account to the db that will be zipped
    with Session(actual_engine) as session:
        acct = Accounts(
            id="test-checking-zip-001",
            name=SAMPLE_QFX_ACCOUNT_ID,
            offbudget=0,
            closed=0,
        )
        session.add(acct)
        session.commit()

    # Locate the sqlite file that was created by actual_engine
    db_path = tmp_path / "db.sqlite"

    metadata = {
        "cloudFileId": "test-cloud-file-id-001",
        "budgetName": "Test Budget",
        "groupId": "test-group-id-001",
        "userId": "test-user",
    }
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(json.dumps(metadata))

    zip_path = tmp_path / "test_budget.actual"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(db_path, "db.sqlite")
        zf.write(metadata_path, "metadata.json")

    return zip_path
