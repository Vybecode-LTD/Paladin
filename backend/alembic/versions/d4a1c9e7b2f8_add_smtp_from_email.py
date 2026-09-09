"""add from_email to smtp_settings

The demo-reply sender address used to be fixed in code (info@ashfordbriggs.com).
Mail providers reject a From address the authenticated account does not own
(seen on the dev server: "553 5.7.1 Sender address rejected: not owned by
user"), so the address is now admin-configurable alongside the other SMTP
settings. Empty means "use the default", which keeps the old behaviour for
existing rows.

Revision ID: d4a1c9e7b2f8
Revises: c7e2f8a41b6d
Create Date: 2026-09-09 04:10:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'd4a1c9e7b2f8'
down_revision = 'c7e2f8a41b6d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # server_default='' backfills the existing (singleton) row so the NOT NULL
    # add is safe; then drop the default so the ORM default governs, matching
    # how the other smtp_settings columns were added.
    op.add_column(
        'smtp_settings',
        sa.Column('from_email', sa.String(length=255), nullable=False, server_default=''),
    )
    op.alter_column('smtp_settings', 'from_email', server_default=None)


def downgrade() -> None:
    op.drop_column('smtp_settings', 'from_email')
