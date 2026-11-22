"""
Transactions API Router
Transaction categorization, manual editing, bulk updates, transaction splitting, and distribution totals.
Strict owner checks on every query (IDOR secure).
"""

from io import StringIO
from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.models import AuditLog, Document, Transaction, User
from app.db.session import get_db
from app.schemas.transaction import (
    BulkCategoriseRequest,
    CategorySummaryResponse,
    CategoryTotalItem,
    TransactionOut,
    TransactionSplitRequest,
    TransactionUpdate,
)
from app.services.categorisation.transaction_classifier import (
    CATEGORIES_META,
    TransactionClassifier,
    detect_duplicate_or_reversal,
)
from app.services.extraction.normalizer import parse_inr_amount

router = APIRouter(prefix="/transactions", tags=["Expense & Transaction Categorisation"])


@router.get("", response_model=List[TransactionOut])
def list_transactions(
    financial_year: Optional[str] = "2025-26",
    category: Optional[str] = None,
    deduction_status: Optional[str] = None,
    search: Optional[str] = None,
    tax_eligible_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists transactions with rich filtering, searching, and sorting."""
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    if financial_year:
        query = query.filter(Transaction.financial_year == financial_year)
    if category:
        query = query.filter(Transaction.category == category)
    if deduction_status:
        query = query.filter(Transaction.deduction_status == deduction_status)
    if tax_eligible_only:
        query = query.filter(Transaction.is_potentially_tax_eligible == True)
    if search:
        query = query.filter(Transaction.description.ilike(f"%{search.strip()}%"))

    return query.order_by(Transaction.date.desc()).all()


@router.put("/{transaction_id}", response_model=TransactionOut)
def update_transaction(
    transaction_id: str,
    payload: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually recategorizes a transaction.
    Optionally applies category change to all similar transactions with matching description.
    """
    tx = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id,
    ).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")

    if payload.category:
        tx.category = payload.category
        tx.classification_source = "user"
        tx.confidence = 1.0
        meta = CATEGORIES_META.get(payload.category, {})
        tx.is_potentially_tax_eligible = meta.get("tax_eligible", False)
        tx.applicable_section = meta.get("section")
        if payload.deduction_status:
            tx.deduction_status = payload.deduction_status
        elif tx.is_potentially_tax_eligible:
            tx.deduction_status = "claimed"
        else:
            tx.deduction_status = "ineligible"

    if payload.deduction_status and not payload.category:
        tx.deduction_status = payload.deduction_status

    # Apply to similar transactions if requested
    updated_similar_count = 0
    if payload.apply_to_similar and payload.category:
        similars = db.query(Transaction).filter(
            Transaction.user_id == current_user.id,
            Transaction.id != tx.id,
            Transaction.description.ilike(f"%{tx.description.strip()[:20]}%"),
        ).all()
        for s in similars:
            s.category = payload.category
            s.classification_source = "user"
            s.confidence = 1.0
            meta = CATEGORIES_META.get(payload.category, {})
            s.is_potentially_tax_eligible = meta.get("tax_eligible", False)
            s.applicable_section = meta.get("section")
            s.deduction_status = tx.deduction_status
            updated_similar_count += 1

    audit = AuditLog(
        user_id=current_user.id,
        action="TRANSACTION_RECATEGORIZED",
        details={"transaction_id": tx.id, "category": tx.category, "similar_updated": updated_similar_count},
    )
    db.add(audit)
    db.commit()
    db.refresh(tx)
    return tx


@router.post("/bulk-categorise")
def bulk_categorise_transactions(
    payload: BulkCategoriseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bulk recategorizes all transactions matching a description keyword or pattern."""
    pattern = payload.description_pattern.strip()
    matched = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.description.ilike(f"%{pattern}%"),
    ).all()

    meta = CATEGORIES_META.get(payload.new_category, {})
    for t in matched:
        t.category = payload.new_category
        t.classification_source = "user"
        t.confidence = 1.0
        t.is_potentially_tax_eligible = meta.get("tax_eligible", False)
        t.applicable_section = meta.get("section")
        t.deduction_status = "claimed" if t.is_potentially_tax_eligible else "ineligible"

    db.commit()
    return {"message": f"Successfully updated {len(matched)} transactions to category '{payload.new_category}'."}


@router.post("/{transaction_id}/split", response_model=List[TransactionOut])
def split_transaction(
    transaction_id: str,
    payload: TransactionSplitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Splits a single transaction into multiple line items
    (e.g. Home Loan EMI split into 80C Principal and 24(b) Interest).
    """
    parent = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id,
    ).first()
    if not parent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")

    total_split_amount = sum(s.amount for s in payload.splits)
    if round(total_split_amount, 2) != round(parent.amount, 2):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sum of split amounts (₹{total_split_amount:,.2f}) must equal parent amount (₹{parent.amount:,.2f}).",
        )

    # Delete existing child splits if re-splitting
    db.query(Transaction).filter(Transaction.parent_transaction_id == parent.id).delete()

    created_children = []
    for s in payload.splits:
        meta = CATEGORIES_META.get(s.category, {})
        child = Transaction(
            user_id=current_user.id,
            document_id=parent.document_id,
            financial_year=parent.financial_year,
            date=parent.date,
            description=s.description or f"{parent.description} [{s.category}]",
            amount=s.amount,
            transaction_type=parent.transaction_type,
            category=s.category,
            confidence=1.0,
            classification_source="user",
            is_potentially_tax_eligible=meta.get("tax_eligible", False),
            applicable_section=meta.get("section"),
            deduction_status="claimed" if meta.get("tax_eligible") else "ineligible",
            parent_transaction_id=parent.id,
        )
        db.add(child)
        created_children.append(child)

    # Mark parent as split / ignored in calculations
    parent.deduction_status = "ignored"
    db.commit()
    for c in created_children:
        db.refresh(c)
    return created_children


@router.get("/category-totals", response_model=CategorySummaryResponse)
def get_category_totals(
    financial_year: str = "2025-26",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns totals by category, count, and tax-deductible summary for charts."""
    txs = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.financial_year == financial_year,
        Transaction.deduction_status != "ignored",
        Transaction.is_duplicate == False,
    ).all()

    cat_map = {}
    total_exp = 0.0
    total_tax_deductible = 0.0

    for t in txs:
        cat = t.category
        if cat not in cat_map:
            meta = CATEGORIES_META.get(cat, {})
            cat_map[cat] = {
                "category": cat,
                "total_amount": 0.0,
                "count": 0,
                "tax_eligible_amount": 0.0,
                "applicable_section": meta.get("section"),
            }
        cat_map[cat]["total_amount"] += t.amount
        cat_map[cat]["count"] += 1
        total_exp += t.amount

        if t.is_potentially_tax_eligible and t.deduction_status in ["claimed", "needs_proof"]:
            cat_map[cat]["tax_eligible_amount"] += t.amount
            total_tax_deductible += t.amount

    items = [CategoryTotalItem(**v) for v in cat_map.values()]
    return CategorySummaryResponse(
        financial_year=financial_year,
        total_expenses=round(total_exp, 2),
        total_tax_deductible_expenses=round(total_tax_deductible, 2),
        categories=sorted(items, key=lambda x: x.total_amount, reverse=True),
    )
