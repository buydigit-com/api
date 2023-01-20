"""empty message

Revision ID: 84bd6fa1cdec
Revises: 120f5723396b
Create Date: 2023-01-20 13:20:09.081115

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '84bd6fa1cdec'
down_revision = '120f5723396b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('transaction', 'description')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('transaction', sa.Column('description', mysql.VARCHAR(length=255), nullable=False))
    # ### end Alembic commands ###