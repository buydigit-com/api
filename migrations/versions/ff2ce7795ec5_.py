"""empty message

Revision ID: ff2ce7795ec5
Revises: 14192a61b91c
Create Date: 2023-01-20 14:49:05.913382

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ff2ce7795ec5'
down_revision = '14192a61b91c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('network', sa.Column('explorer_url', sa.String(length=255), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('network', 'explorer_url')
    # ### end Alembic commands ###