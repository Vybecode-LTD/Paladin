"""add smtp_settings table and demo_requests reply-tracking columns

Adds a company-wide SMTP connection config table (singleton in practice —
the app only ever reads/writes one row) for the admin-configurable
demo-request reply feature, plus the audit-trail columns on demo_requests
that record when/what/who replied.

Revision ID: c7e2f8a41b6d
Revises: b2f4c7a19d3e
Create Date: 2026-07-09 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'c7e2f8a41b6d'
down_revision = 'b2f4c7a19d3e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'smtp_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('host', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('port', sa.Integer(), nullable=False, server_default='587'),
        sa.Column('username', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('encrypted_password', sa.String(length=500), nullable=True),
        sa.Column('use_tls', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('from_name', sa.String(length=200), nullable=False, server_default=''),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                   server_default=sa.func.now()),
    )
    op.alter_column('smtp_settings', 'host', server_default=None)
    op.alter_column('smtp_settings', 'port', server_default=None)
    op.alter_column('smtp_settings', 'username', server_default=None)
    op.alter_column('smtp_settings', 'use_tls', server_default=None)
    op.alter_column('smtp_settings', 'from_name', server_default=None)
    op.alter_column('smtp_settings', 'updated_at', server_default=None)

    op.add_column('demo_requests', sa.Column('replied_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('demo_requests', sa.Column('reply_body', sa.Text(), nullable=True))
    op.add_column('demo_requests', sa.Column('replied_by_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        op.f('fk_demo_requests_replied_by_id_users'),
        'demo_requests', 'users', ['replied_by_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint(op.f('fk_demo_requests_replied_by_id_users'), 'demo_requests', type_='foreignkey')
    op.drop_column('demo_requests', 'replied_by_id')
    op.drop_column('demo_requests', 'reply_body')
    op.drop_column('demo_requests', 'replied_at')
    op.drop_table('smtp_settings')
