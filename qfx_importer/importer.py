"""Core QFX/OFX import logic, decoupled from the web layer.

This module contains pure, testable functions for:
- Parsing QFX/OFX file content into structured data
- Importing parsed transactions into an Actual Budget SQLAlchemy session
"""
import logging
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from io import BytesIO
from typing import Optional

import ofxparse
from actual.database import Accounts
from actual.queries import create_transaction
from sqlmodel import Session

logger = logging.getLogger(__name__)


@dataclass
class ParsedTransaction:
    """A single transaction extracted from a QFX/OFX file."""

    fitid: str
    date: date
    amount: Decimal
    memo: str
    payee: Optional[str] = None


@dataclass
class ParsedAccount:
    """An account block extracted from a QFX/OFX file."""

    account_id: str
    transactions: list[ParsedTransaction] = field(default_factory=list)


@dataclass
class ImportResult:
    """Result of importing one file into an Actual Budget session."""

    filename: str
    imported_count: int = 0
    skipped_count: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.skipped_count == 0 and not self.errors


def parse_qfx(content: bytes) -> list[ParsedAccount]:
    """Parse QFX/OFX file *content* and return a list of :class:`ParsedAccount` objects.

    :param content: Raw bytes of a ``.qfx`` or ``.ofx`` file.
    :returns: List of accounts, each containing the parsed transactions.
    :raises ofxparse.OfxParserException: If the file is not valid OFX/QFX.
    """
    ofx = ofxparse.OfxParser.parse(BytesIO(content))
    raw_account = ofx.account

    if raw_account is None:
        return []

    accounts = raw_account if isinstance(raw_account, list) else [raw_account]

    result: list[ParsedAccount] = []
    for account in accounts:
        account_id: str = getattr(account, "account_id", "") or ""
        transactions: list[ParsedTransaction] = []

        for txn in account.statement.transactions:
            txn_date = txn.date
            if hasattr(txn_date, "date"):
                txn_date = txn_date.date()

            transactions.append(
                ParsedTransaction(
                    fitid=str(getattr(txn, "id", "") or ""),
                    date=txn_date,
                    amount=Decimal(str(txn.amount)),
                    memo=str(getattr(txn, "memo", "") or ""),
                    payee=str(getattr(txn, "payee", "") or "") or None,
                )
            )

        result.append(ParsedAccount(account_id=account_id, transactions=transactions))

    return result


def import_transactions(
    session: Session,
    account: Accounts,
    transactions: list[ParsedTransaction],
    filename: str = "",
) -> ImportResult:
    """Import a list of :class:`ParsedTransaction` objects into an Actual Budget *session*.

    Each transaction is created via :func:`actual.queries.create_transaction`.
    Errors for individual rows are captured and the import continues.

    :param session: An open SQLAlchemy session connected to an Actual Budget SQLite database.
    :param account: The :class:`actual.database.Accounts` object to post transactions to.
    :param transactions: List of parsed transactions from :func:`parse_qfx`.
    :param filename: Optional filename used for result reporting only.
    :returns: :class:`ImportResult` with import counts and any per-row errors.
    """
    result = ImportResult(filename=filename)

    for txn in transactions:
        try:
            create_transaction(
                session,
                date=txn.date,
                account=account,
                payee=txn.payee,
                notes=txn.memo,
                amount=float(txn.amount),
                imported_id=txn.fitid or None,
                imported_payee=txn.payee,
            )
            result.imported_count += 1
        except Exception as exc:
            logger.warning(
                "Skipping transaction fitid=%s in %s: %s",
                txn.fitid,
                filename,
                exc,
            )
            result.errors.append(
                f"Could not import transaction {txn.fitid!r}: {exc}"
            )
            result.skipped_count += 1

    return result
