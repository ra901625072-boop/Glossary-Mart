"""Add created_at to coupons

Revision ID: a1c4e92d8f33
Revises: 0b02b8fe2d1b
Create Date: 2026-09-10 17:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1c4e92d8f33'
down_revision = '0b02b8fe2d1b'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('coupons')]
    if 'created_at' not in columns:
        with op.batch_alter_table('coupons', schema=None) as batch_op:
            batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('coupons', schema=None) as batch_op:
        batch_op.drop_column('created_at')
