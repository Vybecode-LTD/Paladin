"""add cover_image_svg to blog_posts

Adds a Text column holding an AI-generated, sanitized vector (SVG) blog header.
Separate from cover_image_url (String(500)) because an SVG is far larger and is
a distinct concept from a pasted external image URL.

Revision ID: b2f4c7a19d3e
Revises: 109933857eb1
Create Date: 2026-07-09 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'b2f4c7a19d3e'
down_revision = '109933857eb1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # server_default='' backfills existing rows so the NOT NULL add is safe;
    # dropped immediately after so the app-level default ("") is the sole source.
    op.add_column(
        'blog_posts',
        sa.Column('cover_image_svg', sa.Text(), nullable=False, server_default=''),
    )
    op.alter_column('blog_posts', 'cover_image_svg', server_default=None)


def downgrade() -> None:
    op.drop_column('blog_posts', 'cover_image_svg')
