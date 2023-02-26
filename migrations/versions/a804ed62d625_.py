"""empty message

Revision ID: a804ed62d625
Revises: 574e53be4d73
Create Date: 2023-02-24 16:56:07.794139

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a804ed62d625'
down_revision = '574e53be4d73'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('deposit', sa.Column('amount_generated_at', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('deposit', 'amount_generated_at')
    # ### end Alembic commands ###
