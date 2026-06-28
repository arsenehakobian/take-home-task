"""Add role to User

Revision ID: b7c4f2a9d130
Revises: fe56fa70289e
Create Date: 2026-06-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7c4f2a9d130'
down_revision = 'fe56fa70289e'
branch_labels = None
depends_on = None


def upgrade():
    # Add nullable first so existing rows can be backfilled before NOT NULL.
    op.add_column('user', sa.Column('role', sa.String(length=20), nullable=True))
    # Backfill: superusers become admins, everyone else a member.
    op.execute(
        "UPDATE \"user\" SET role = CASE WHEN is_superuser THEN 'admin' ELSE 'member' END"
    )
    op.alter_column('user', 'role', existing_type=sa.String(length=20), nullable=False)


def downgrade():
    op.drop_column('user', 'role')
