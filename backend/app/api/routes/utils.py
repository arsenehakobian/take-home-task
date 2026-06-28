from fastapi import APIRouter, Depends
from pydantic.networks import EmailStr
from sqlmodel import col, func, select

from app.api.deps import SessionDep, get_current_active_superuser, require_role
from app.models import Message, User, UserMetrics, UserRole
from app.utils import generate_test_email, send_email

router = APIRouter(prefix="/utils", tags=["utils"])


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get(
    "/metrics",
    dependencies=[Depends(require_role(UserRole.MANAGER))],
)
def read_metrics(session: SessionDep) -> UserMetrics:
    """
    Read-only user metrics for managers and admins.
    """
    total_users = session.exec(select(func.count()).select_from(User)).one()
    active_users = session.exec(
        select(func.count()).select_from(User).where(col(User.is_active).is_(True))
    ).one()
    return UserMetrics(total_users=total_users, active_users=active_users)


@router.get("/health-check/")
async def health_check() -> bool:
    return True
