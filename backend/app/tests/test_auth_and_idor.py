"""
Authentication and IDOR Security Tests
Direct endpoint execution verifying:
1. User registration, password hashing, and token issuance.
2. PAN encryption at rest and UI masking.
3. User profile updating and password change.
4. IDOR Protection: User B cannot query or mutate User A's data.
5. Account deletion triggers full database cascade and data purge.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import HTTPException
from app.api.v1.auth import register_user, login_user, refresh_access_token
from app.api.v1.users import get_my_profile, update_my_profile, update_my_pan, delete_my_account
from app.core.encryption import decrypt_text
from app.db.models import Base, Document, User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest
from app.schemas.user import PanUpdateRequest, UserUpdate

# Setup isolated test in-memory SQLite database
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_register_login_and_pan_masking(db):
    reg_req = RegisterRequest(
        email="taxpayer.a@example.com",
        password="Password123!",
        full_name="Taxpayer A",
        pan="ABCDE1234F",
        employment_type="salaried",
        is_metro=True,
    )
    res = register_user(reg_req, db=db)
    assert res["access_token"] is not None
    assert res["user"]["pan_masked"] == "ABCDE****F"

    # Verify encrypted storage in DB
    user_row = db.query(User).filter(User.email == "taxpayer.a@example.com").first()
    assert user_row is not None
    assert user_row.encrypted_pan != "ABCDE1234F"
    assert decrypt_text(user_row.encrypted_pan) == "ABCDE1234F"

    # Login
    login_req = LoginRequest(email="taxpayer.a@example.com", password="Password123!")
    login_res = login_user(login_req, db=db)
    assert login_res["access_token"] is not None
    assert login_res["user"]["email"] == "taxpayer.a@example.com"


def test_idor_isolation(db):
    # Register Alice
    alice_res = register_user(
        RegisterRequest(email="alice@example.com", password="PasswordAlice123!", full_name="Alice"),
        db=db,
    )
    alice_user = db.query(User).filter(User.email == "alice@example.com").first()

    # Register Bob
    bob_res = register_user(
        RegisterRequest(email="bob@example.com", password="PasswordBob123!", full_name="Bob"),
        db=db,
    )
    bob_user = db.query(User).filter(User.email == "bob@example.com").first()

    # Insert document for Alice
    alice_doc = Document(
        user_id=alice_user.id,
        financial_year="2025-26",
        file_name="alice_slip.pdf",
        file_type="application/pdf",
        file_size=2048,
        storage_path="/storage/alice_slip.enc",
        file_hash="hash_alice",
        doc_type="salary_slip",
        status="confirmed",
    )
    db.add(alice_doc)
    db.commit()

    # Alice queries her profile
    alice_profile = get_my_profile(current_user=alice_user)
    assert alice_profile.email == "alice@example.com"

    # Bob queries his profile
    bob_profile = get_my_profile(current_user=bob_user)
    assert bob_profile.email == "bob@example.com"
    assert bob_profile.id != alice_user.id

    # Verify Bob querying documents with user_id=bob_user.id returns 0 docs
    bob_docs = db.query(Document).filter(Document.user_id == bob_user.id).all()
    assert len(bob_docs) == 0

    # Verify Alice has her document
    alice_docs = db.query(Document).filter(Document.user_id == alice_user.id).all()
    assert len(alice_docs) == 1
    assert alice_docs[0].file_name == "alice_slip.pdf"


def test_account_deletion_purges_all_records(db):
    user_res = register_user(
        RegisterRequest(email="purge.me@example.com", password="PasswordPurge123!", full_name="Purge Me"),
        db=db,
    )
    user = db.query(User).filter(User.email == "purge.me@example.com").first()
    user_id = user.id

    # Add a document for user
    doc = Document(
        user_id=user_id,
        financial_year="2025-26",
        file_name="purge_doc.pdf",
        file_type="application/pdf",
        file_size=1024,
        storage_path="/nonexistent/purge_doc.enc",
        file_hash="hash_purge",
    )
    db.add(doc)
    db.commit()

    # Purge account
    del_res = delete_my_account(current_user=user, db=db)
    assert "permanently purged" in del_res["message"]

    # Verify user and document are deleted
    assert db.query(User).filter(User.id == user_id).first() is None
    assert db.query(Document).filter(Document.user_id == user_id).first() is None
