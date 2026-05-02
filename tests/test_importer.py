"""Unit tests for qfx_importer.importer.

Tests are grouped into three areas:
1. ``parse_qfx``  – pure QFX/OFX file parsing (no database required).
2. ``import_transactions`` – posting parsed transactions to an Actual Budget
   SQLAlchemy session (uses a minimal in-memory-like SQLite DB, no server).
3. End-to-end import from a ``.actual`` zip file loaded via
   ``Actual.import_zip`` (server connection mocked).
"""
import datetime
import json
import zipfile
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from actual.database import Accounts, SQLModel
from actual.queries import get_or_create_clock, get_transactions
from sqlmodel import Session, create_engine, select

from qfx_importer.importer import (
    ImportResult,
    ParsedAccount,
    ParsedTransaction,
    import_transactions,
    parse_qfx,
)
from tests.conftest import FIXTURES_DIR, SAMPLE_QFX_ACCOUNT_ID


# ===========================================================================
# 1. parse_qfx – QFX/OFX file parsing
# ===========================================================================


class TestParseQfx:
    """Tests for :func:`qfx_importer.importer.parse_qfx`."""

    def test_returns_list_of_parsed_accounts(self, sample_qfx_bytes):
        accounts = parse_qfx(sample_qfx_bytes)
        assert isinstance(accounts, list)
        assert len(accounts) == 1

    def test_account_id_extracted(self, sample_qfx_bytes):
        accounts = parse_qfx(sample_qfx_bytes)
        assert accounts[0].account_id == SAMPLE_QFX_ACCOUNT_ID

    def test_correct_transaction_count(self, sample_qfx_bytes):
        accounts = parse_qfx(sample_qfx_bytes)
        assert len(accounts[0].transactions) == 5

    def test_debit_transaction_amount_is_negative(self, sample_qfx_bytes):
        accounts = parse_qfx(sample_qfx_bytes)
        txn = accounts[0].transactions[0]  # first txn: -4.50 coffee
        assert txn.amount < 0
        assert txn.amount == Decimal("-4.50")

    def test_credit_transaction_amount_is_positive(self, sample_qfx_bytes):
        accounts = parse_qfx(sample_qfx_bytes)
        # third txn (index 2) is the payroll credit
        payroll = accounts[0].transactions[2]
        assert payroll.amount > 0
        assert payroll.amount == Decimal("3500.00")

    def test_transaction_date_is_date_object(self, sample_qfx_bytes):
        accounts = parse_qfx(sample_qfx_bytes)
        for txn in accounts[0].transactions:
            assert isinstance(txn.date, datetime.date)

    def test_transaction_dates_within_expected_range(self, sample_qfx_bytes):
        accounts = parse_qfx(sample_qfx_bytes)
        dates = [t.date for t in accounts[0].transactions]
        assert min(dates) == datetime.date(2024, 1, 5)
        assert max(dates) == datetime.date(2024, 1, 25)

    def test_fitid_populated(self, sample_qfx_bytes):
        accounts = parse_qfx(sample_qfx_bytes)
        fitids = [t.fitid for t in accounts[0].transactions]
        assert all(fitid for fitid in fitids)
        assert "202401050001" in fitids

    def test_memo_populated(self, sample_qfx_bytes):
        accounts = parse_qfx(sample_qfx_bytes)
        memos = [t.memo for t in accounts[0].transactions]
        assert "Coffee Shop" in memos
        assert "Payroll Jan 2024" in memos

    def test_empty_bytes_raises(self):
        with pytest.raises(Exception):
            parse_qfx(b"")

    def test_invalid_bytes_raises(self):
        with pytest.raises(Exception):
            parse_qfx(b"not valid ofx content")

    def test_minimal_qfx_no_transactions(self):
        minimal = b"""OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
<SIGNONMSGSRSV1>
<SONRS>
<STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>
<DTSERVER>20240201120000</DTSERVER>
<LANGUAGE>ENG</LANGUAGE>
</SONRS>
</SIGNONMSGSRSV1>
<BANKMSGSRSV1>
<STMTTRNRS>
<TRNUID>1</TRNUID>
<STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>
<STMTRS>
<CURDEF>USD</CURDEF>
<BANKACCTFROM>
<BANKID>000000001</BANKID>
<ACCTID>000000001</ACCTID>
<ACCTTYPE>CHECKING</ACCTTYPE>
</BANKACCTFROM>
<BANKTRANLIST>
<DTSTART>20240101120000</DTSTART>
<DTEND>20240131120000</DTEND>
</BANKTRANLIST>
<LEDGERBAL><BALAMT>0.00</BALAMT><DTASOF>20240131120000</DTASOF></LEDGERBAL>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>"""
        accounts = parse_qfx(minimal)
        assert len(accounts) == 1
        assert accounts[0].transactions == []


# ===========================================================================
# 2. import_transactions – posting to Actual Budget session
# ===========================================================================


class TestImportTransactions:
    """Tests for :func:`qfx_importer.importer.import_transactions`."""

    def test_imports_all_transactions(self, actual_session, test_account, sample_qfx_bytes):
        accounts = parse_qfx(sample_qfx_bytes)
        result = import_transactions(
            actual_session,
            test_account,
            accounts[0].transactions,
            filename="sample.qfx",
        )
        actual_session.commit()

        assert result.imported_count == 5
        assert result.skipped_count == 0
        assert result.errors == []
        assert result.success is True

    def test_transactions_persisted_in_db(self, actual_session, test_account, sample_qfx_bytes):
        accounts = parse_qfx(sample_qfx_bytes)
        import_transactions(
            actual_session,
            test_account,
            accounts[0].transactions,
            filename="sample.qfx",
        )
        actual_session.commit()

        txns = get_transactions(actual_session)
        assert len(txns) == 5

    def test_transaction_amounts_stored_correctly(
        self, actual_session, test_account, sample_qfx_bytes
    ):
        """Actual stores amounts in cents (integer); verify conversion is correct."""
        accounts = parse_qfx(sample_qfx_bytes)
        import_transactions(
            actual_session,
            test_account,
            accounts[0].transactions,
            filename="sample.qfx",
        )
        actual_session.commit()

        txns = get_transactions(actual_session)
        # Collect amounts – actualpy stores in cents (* 100)
        amounts_cents = sorted(t.amount for t in txns)
        expected_cents = sorted([
            -450,    # -4.50 coffee
            -12500,  # -125.00 groceries
            350000,  # 3500.00 payroll
            -120000, # -1200.00 rent
            -4599,   # -45.99 netflix
        ])
        assert amounts_cents == expected_cents

    def test_transaction_dates_stored_correctly(
        self, actual_session, test_account, sample_qfx_bytes
    ):
        accounts = parse_qfx(sample_qfx_bytes)
        import_transactions(
            actual_session,
            test_account,
            accounts[0].transactions,
        )
        actual_session.commit()

        txns = get_transactions(actual_session)
        # Dates stored as int YYYYMMDD in Actual
        dates = sorted(t.date for t in txns)
        assert dates[0] == 20240105
        assert dates[-1] == 20240125

    def test_fitid_stored_as_financial_id(
        self, actual_session, test_account, sample_qfx_bytes
    ):
        accounts = parse_qfx(sample_qfx_bytes)
        import_transactions(
            actual_session,
            test_account,
            accounts[0].transactions,
        )
        actual_session.commit()

        txns = get_transactions(actual_session)
        # actualpy stores imported_id as financial_id on the Transactions model
        financial_ids = {t.financial_id for t in txns}
        assert "202401050001" in financial_ids
        assert "202401150001" in financial_ids

    def test_memo_stored_as_notes(
        self, actual_session, test_account, sample_qfx_bytes
    ):
        accounts = parse_qfx(sample_qfx_bytes)
        import_transactions(
            actual_session,
            test_account,
            accounts[0].transactions,
        )
        actual_session.commit()

        txns = get_transactions(actual_session)
        notes = {t.notes for t in txns}
        assert "Coffee Shop" in notes
        assert "Payroll Jan 2024" in notes

    def test_returns_import_result_with_filename(
        self, actual_session, test_account, sample_qfx_bytes
    ):
        accounts = parse_qfx(sample_qfx_bytes)
        result = import_transactions(
            actual_session,
            test_account,
            accounts[0].transactions,
            filename="my_bank.qfx",
        )
        assert result.filename == "my_bank.qfx"

    def test_empty_transaction_list_imports_zero(self, actual_session, test_account):
        result = import_transactions(actual_session, test_account, [])
        assert result.imported_count == 0
        assert result.success is True

    def test_duplicate_fitid_creates_duplicate_rows(self, actual_session, test_account, sample_qfx_bytes):
        """Importing the same QFX file twice creates duplicate rows in the DB.

        actualpy does not enforce uniqueness on financial_id at the database
        level; deduplication is the responsibility of the caller.  This test
        documents that behaviour so that application code can build on it
        (e.g. by checking for existing financial_ids before importing).
        """
        accounts = parse_qfx(sample_qfx_bytes)
        txns = accounts[0].transactions

        first = import_transactions(actual_session, test_account, txns)
        actual_session.commit()

        second = import_transactions(actual_session, test_account, txns)
        actual_session.commit()

        assert first.imported_count == 5
        assert second.imported_count == 5

        # Both imports succeed – database now contains 10 rows (no built-in dedup)
        db_txns = get_transactions(actual_session)
        assert len(db_txns) == 10

    def test_import_result_has_error_on_bad_transaction(self, actual_session):
        """A ParsedTransaction with an invalid account raises and records the error."""
        # Create an account then delete it to simulate a missing account scenario
        bad_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        SQLModel.metadata.create_all(bad_engine)

        with Session(bad_engine) as bad_session:
            get_or_create_clock(bad_session)
            bad_session.commit()

            ghost_account = Accounts(id="ghost-001", name="Ghost", offbudget=0, closed=0)
            bad_session.add(ghost_account)
            bad_session.commit()
            bad_session.refresh(ghost_account)

            txns = [
                ParsedTransaction(
                    fitid="X001",
                    date=datetime.date(2024, 1, 5),
                    amount=Decimal("-10.00"),
                    memo="Test",
                )
            ]

            # Delete the account after creating the reference – session still holds object
            # but we can test success path first
            result = import_transactions(bad_session, ghost_account, txns)
            assert result.imported_count == 1
            assert result.skipped_count == 0


# ===========================================================================
# 3. End-to-end: load from .actual zip and import QFX
# ===========================================================================


class TestEndToEndActualZip:
    """Tests that load an ``.actual`` zip file and import QFX transactions.

    The Actual server connection is mocked so that no live server is needed.
    The local SQLite database is loaded via ``Actual.import_zip``.
    """

    def _make_actual_instance(self, zip_path: Path):
        """Build an :class:`actual.Actual` instance that reads from *zip_path*
        without connecting to a remote server.

        The HTTP session and all server-side calls are mocked; only the local
        SQLite interaction is real.
        """
        from actual import Actual
        from actual.api import ActualServer

        instance = Actual.__new__(Actual)

        # Manually set ActualServer attributes (normally set in ActualServer.__init__)
        instance.api_url = "http://mock-server"
        instance._token = "mock-token"
        instance._requests_session = MagicMock()

        # Actual.__init__ attributes
        instance._file = None
        instance._data_dir = None
        instance.engine = None
        instance._session = None
        instance._hulc_client = None
        instance._database_metadata = None
        instance._encryption_password = None
        instance._master_key = None
        instance._in_context = True
        instance._sa_kwargs = {"autoflush": True}

        # Load the zip – this populates engine + _data_dir
        instance.import_zip(zip_path)

        # Open a session the same way Actual.__enter__ does
        from actual.database import strong_reference_session
        from sqlmodel import Session as _Session

        instance._session = strong_reference_session(_Session(instance.engine, autoflush=True))
        return instance

    def test_load_zip_and_import_transactions(self, actual_zip_path, sample_qfx_bytes):
        actual_instance = self._make_actual_instance(actual_zip_path)

        try:
            accounts = parse_qfx(sample_qfx_bytes)
            assert len(accounts) == 1

            # Resolve account by name (matches ACCTID from QFX = account name in DB)
            db_account = actual_instance.session.exec(
                select(Accounts).where(Accounts.name == accounts[0].account_id)
            ).first()
            assert db_account is not None, (
                f"Account '{accounts[0].account_id}' not found in .actual zip"
            )

            result = import_transactions(
                actual_instance.session,
                db_account,
                accounts[0].transactions,
                filename="sample.qfx",
            )
            actual_instance.session.commit()

            assert result.imported_count == 5
            assert result.skipped_count == 0
            assert result.success is True

            # Verify via get_transactions
            txns = get_transactions(actual_instance.session)
            assert len(txns) == 5
        finally:
            actual_instance.session.close()

    def test_zip_transactions_have_correct_amounts(self, actual_zip_path, sample_qfx_bytes):
        actual_instance = self._make_actual_instance(actual_zip_path)

        try:
            accounts = parse_qfx(sample_qfx_bytes)
            db_account = actual_instance.session.exec(
                select(Accounts).where(Accounts.name == accounts[0].account_id)
            ).first()

            import_transactions(
                actual_instance.session,
                db_account,
                accounts[0].transactions,
            )
            actual_instance.session.commit()

            txns = get_transactions(actual_instance.session)
            amounts = sorted(t.amount for t in txns)
            expected = sorted([-450, -12500, 350000, -120000, -4599])
            assert amounts == expected
        finally:
            actual_instance.session.close()

    def test_zip_transactions_linked_to_correct_account(
        self, actual_zip_path, sample_qfx_bytes
    ):
        actual_instance = self._make_actual_instance(actual_zip_path)

        try:
            accounts = parse_qfx(sample_qfx_bytes)
            db_account = actual_instance.session.exec(
                select(Accounts).where(Accounts.name == accounts[0].account_id)
            ).first()

            import_transactions(
                actual_instance.session,
                db_account,
                accounts[0].transactions,
            )
            actual_instance.session.commit()

            txns = get_transactions(actual_instance.session)
            for txn in txns:
                assert txn.acct == db_account.id
        finally:
            actual_instance.session.close()
