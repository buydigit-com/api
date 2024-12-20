"""empty message

Revision ID: 574e53be4d73
Revises: ff2ce7795ec5
Create Date: 2023-01-21 19:32:25.110834

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '574e53be4d73'
down_revision = 'ff2ce7795ec5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('deposit', sa.Column('confirmed_at', sa.DateTime(), nullable=True))
    op.add_column('deposit', sa.Column('user_address', sa.String(length=255), nullable=True))
    op.drop_column('deposit', 'amount_timestamp')
    op.add_column('dump', sa.Column('dumped_at', sa.DateTime(), nullable=True))
    op.drop_constraint('dump_ibfk_2', 'dump', type_='foreignkey')
    op.drop_constraint('dump_ibfk_1', 'dump', type_='foreignkey')
    op.drop_column('dump', 'coin_id')
    op.drop_column('dump', 'network_id')
    op.drop_column('dump', 'dump_timestamp')
    op.add_column('shop', sa.Column('theme_customization', sa.JSON(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('shop', 'theme_customization')
    op.add_column('dump', sa.Column('dump_timestamp', mysql.DATETIME(), nullable=True))
    op.add_column('dump', sa.Column('network_id', mysql.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('dump', sa.Column('coin_id', mysql.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('dump_ibfk_1', 'dump', 'coin', ['coin_id'], ['id'])
    op.create_foreign_key('dump_ibfk_2', 'dump', 'network', ['network_id'], ['id'])
    op.drop_column('dump', 'dumped_at')
    op.add_column('deposit', sa.Column('amount_timestamp', mysql.DATETIME(), nullable=True))
    op.drop_column('deposit', 'user_address')
    op.drop_column('deposit', 'confirmed_at')
    # ### end Alembic commands ###
