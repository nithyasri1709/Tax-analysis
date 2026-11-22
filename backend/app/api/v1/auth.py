"""
Authentication Router
Register, Login, Token Refresh, Logout with revocation.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.encryption import encrypt_text, mask_pan
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    hash_refresh_token,
    verify_password,
)
from app.db.models import AuditLog, FinancialProfile, RefreshToken, User
from app.db.session import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Registers a new user and issues JWT tokens."""
    existing = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    enc_pan = None
    masked_pan = None
    if payload.pan:
        enc_pan = encrypt_text(payload.pan.upper().strip())
        masked_pan = mask_pan(payload.pan)

    new_user = User(
        email=payload.email.lower().strip(),
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name.strip(),
        dob=payload.dob,
        age_bracket=payload.age_bracket,
        residential_status=payload.residential_status,
        state=payload.state,
        city=payload.city,
        is_metro=payload.is_metro,
        employment_type=payload.employment_type,
        encrypted_pan=enc_pan,
        pan_masked=masked_pan,
    )
    db.add(new_user)
    db.flush()

    # Create default financial profiles for current and adjacent years
    for fy in ["2024-25", "2025-26", "2026-27"]:
        prof = FinancialProfile(user_id=new_user.id, financial_year=fy, selected_regime="new")
        db.add(prof)

    # Issue tokens
    access_token = create_access_token(new_user.id)
    raw_refresh, token_hash, expires_at = create_refresh_token(new_user.id)
    refresh_record = RefreshToken(
        user_id=new_user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(refresh_record)

    # Audit log
    audit = AuditLog(
        user_id=new_user.id,
        action="USER_REGISTERED",
        details={"email": new_user.email, "employment_type": new_user.employment_type},
    )
    db.add(audit)
    db.commit()
    db.refresh(new_user)

    user_dict = {
        "id": new_user.id,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "age_bracket": new_user.age_bracket,
        "residential_status": new_user.residential_status,
        "is_metro": new_user.is_metro,
        "employment_type": new_user.employment_type,
        "pan_masked": new_user.pan_masked,
    }

    return {
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "token_type": "bearer",
        "user": user_dict,
    }


@router.post("/login", response_model=TokenResponse)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates user and returns fresh access + refresh tokens."""
    user = db.query(User).filter(User.email == payload.email.lower().strip(), User.is_active == True).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user.id)
    raw_refresh, token_hash, expires_at = create_refresh_token(user.id)
    refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(refresh_record)

    audit = AuditLog(user_id=user.id, action="USER_LOGIN", details={})
    db.add(audit)
    db.commit()

    user_dict = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "age_bracket": user.age_bracket,
        "residential_status": user.residential_status,
        "is_metro": user.is_metro,
        "employment_type": user.employment_type,
        "pan_masked": user.pan_masked,
    }

    return {
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "token_type": "bearer",
        "user": user_dict,
    }


@router.post("/refresh")
def refresh_access_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    """Rotates refresh token and returns new access + refresh tokens."""
    thash = hash_refresh_token(payload.refresh_token)
    token_record = db.query(RefreshToken).filter(
        RefreshToken.token_hash == thash,
        RefreshToken.is_revoked == False,
    ).first()

    now = datetime.now(timezone.utc)
    # Check if timezone naive vs aware
    if token_record and token_record.expires_at.tzinfo is None:
        token_exp = token_record.expires_at.replace(tzinfo=timezone.utc)
    elif token_record:
        token_exp = token_record.expires_at
    else:
        token_exp = None

    if not token_record or token_exp < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    # Revoke old refresh token (rotation)
    token_record.is_revoked = True

    # Issue new pair
    new_access = create_access_token(token_record.user_id)
    raw_new_refresh, new_hash, new_exp = create_refresh_token(token_record.user_id)
    new_record = RefreshToken(
        user_id=token_record.user_id,
        token_hash=new_hash,
        expires_at=new_exp,
    )
    db.add(new_record)
    db.commit()

    return {
        "access_token": new_access,
        "refresh_token": raw_new_refresh,
        "token_type": "bearer",
    }


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout_user(payload: RefreshRequest, db: Session = Depends(get_db)):
    """Revokes the refresh token."""
    thash = hash_refresh_token(payload.refresh_token)
    token_record = db.query(RefreshToken).filter(RefreshToken.token_hash == thash).first()
    if token_record:
        token_record.is_revoked = True
        db.commit()
    return {"message": "Logged out successfully. Refresh token revoked."}
