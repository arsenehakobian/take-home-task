import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.api.deps import require_role
from app.core.config import settings
from app.models import User, UserCreate, UserRole, UserUpdate
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string


def _make_user(db: Session, role: UserRole) -> User:
    user_in = UserCreate(
        email=random_email(), password=random_lower_string(), role=role
    )
    return crud.create_user(session=db, user_create=user_in)


def _role_headers(client: TestClient, db: Session, role: UserRole) -> dict[str, str]:
    email = random_email()
    password = random_lower_string()
    crud.create_user(
        session=db,
        user_create=UserCreate(email=email, password=password, role=role),
    )
    return user_authentication_headers(client=client, email=email, password=password)


# --- require_role factory (no DB needed) ---------------------------------


def _user(role: UserRole, is_superuser: bool = False) -> User:
    return User(
        email="x@example.com",
        hashed_password="x",
        role=role,
        is_superuser=is_superuser,
    )


@pytest.mark.parametrize(
    "role, allowed, expected",
    [
        (UserRole.ADMIN, (UserRole.ADMIN,), True),
        (UserRole.ADMIN, (UserRole.MANAGER,), True),  # admin can do everything
        (UserRole.MANAGER, (UserRole.MANAGER,), True),
        (UserRole.MANAGER, (UserRole.ADMIN,), False),
        (UserRole.MEMBER, (UserRole.MANAGER,), False),
        (UserRole.MEMBER, (UserRole.ADMIN,), False),
    ],
)
def test_require_role_matrix(
    role: UserRole, allowed: tuple[UserRole, ...], expected: bool
) -> None:
    dependency = require_role(*allowed)
    if expected:
        assert dependency(_user(role)) is not None
    else:
        with pytest.raises(HTTPException) as exc:
            dependency(_user(role))
        assert exc.value.status_code == 403


def test_require_role_superuser_always_passes() -> None:
    dependency = require_role(UserRole.MANAGER)
    # A superuser flag promotes regardless of the stored role string.
    assert dependency(_user(UserRole.MEMBER, is_superuser=True)) is not None


# --- crud invariant: role <-> is_superuser -------------------------------


def test_create_admin_role_sets_is_superuser(db: Session) -> None:
    user = _make_user(db, UserRole.ADMIN)
    assert user.role == UserRole.ADMIN
    assert user.is_superuser is True


def test_create_superuser_flag_sets_admin_role(db: Session) -> None:
    user_in = UserCreate(
        email=random_email(), password=random_lower_string(), is_superuser=True
    )
    user = crud.create_user(session=db, user_create=user_in)
    assert user.role == UserRole.ADMIN


def test_update_role_member_demotes_superuser(db: Session) -> None:
    user = _make_user(db, UserRole.ADMIN)
    crud.update_user(
        session=db, db_user=user, user_in=UserUpdate(role=UserRole.MEMBER)
    )
    assert user.is_superuser is False
    assert user.role == UserRole.MEMBER


# --- endpoint authorization ----------------------------------------------


def test_manager_can_list_users(client: TestClient, db: Session) -> None:
    headers = _role_headers(client, db, UserRole.MANAGER)
    r = client.get(f"{settings.API_V1_STR}/users/", headers=headers)
    assert r.status_code == 200


def test_member_cannot_list_users(client: TestClient, db: Session) -> None:
    headers = _role_headers(client, db, UserRole.MEMBER)
    r = client.get(f"{settings.API_V1_STR}/users/", headers=headers)
    assert r.status_code == 403


def test_member_can_read_own_profile(client: TestClient, db: Session) -> None:
    headers = _role_headers(client, db, UserRole.MEMBER)
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert r.status_code == 200


def test_member_cannot_read_other_user(client: TestClient, db: Session) -> None:
    other = _make_user(db, UserRole.MEMBER)
    headers = _role_headers(client, db, UserRole.MEMBER)
    r = client.get(f"{settings.API_V1_STR}/users/{other.id}", headers=headers)
    assert r.status_code == 403


def test_manager_can_read_other_user(client: TestClient, db: Session) -> None:
    other = _make_user(db, UserRole.MEMBER)
    headers = _role_headers(client, db, UserRole.MANAGER)
    r = client.get(f"{settings.API_V1_STR}/users/{other.id}", headers=headers)
    assert r.status_code == 200


def test_manager_cannot_create_user(client: TestClient, db: Session) -> None:
    headers = _role_headers(client, db, UserRole.MANAGER)
    payload = {"email": random_email(), "password": random_lower_string()}
    r = client.post(f"{settings.API_V1_STR}/users/", headers=headers, json=payload)
    assert r.status_code == 403


def test_admin_can_create_user(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    payload = {"email": random_email(), "password": random_lower_string()}
    r = client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=payload
    )
    assert r.status_code == 200


def test_manager_can_view_metrics(client: TestClient, db: Session) -> None:
    headers = _role_headers(client, db, UserRole.MANAGER)
    r = client.get(f"{settings.API_V1_STR}/utils/metrics", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert "total_users" in body
    assert "active_users" in body


def test_member_cannot_view_metrics(client: TestClient, db: Session) -> None:
    headers = _role_headers(client, db, UserRole.MEMBER)
    r = client.get(f"{settings.API_V1_STR}/utils/metrics", headers=headers)
    assert r.status_code == 403