"""empty message

Revision ID: ce363f12e2ee
Revises: 34545e53bae3
Create Date: 2023-01-11 17:15:43.845733

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'ce363f12e2ee'
down_revision = '34545e53bae3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('deposit', sa.Column('status', sa.String(length=255), nullable=False))
    op.drop_column('transaction', 'status')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('transaction', sa.Column('status', mysql.VARCHAR(length=255), nullable=False))
    op.drop_column('deposit', 'status')
    # ### end Alembic commands ###