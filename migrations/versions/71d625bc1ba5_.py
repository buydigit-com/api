"""empty message

Revision ID: 71d625bc1ba5
Revises: 1b6eb5a097f2
Create Date: 2023-01-12 14:29:36.409321

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '71d625bc1ba5'
down_revision = '1b6eb5a097f2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('dump',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=255), nullable=False),
    sa.Column('final_fiat_amount', sa.Float(), nullable=True),
    sa.Column('dump_timestamp', sa.DateTime(), nullable=True),
    sa.Column('fiat_currency', sa.String(length=255), nullable=True),
    sa.Column('coin_id', sa.Integer(), nullable=True),
    sa.Column('network_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['coin_id'], ['coin.id'], ),
    sa.ForeignKeyConstraint(['network_id'], ['network.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('deposit', sa.Column('dump_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'deposit', 'dump', ['dump_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'deposit', type_='foreignkey')
    op.drop_column('deposit', 'dump_id')
    op.drop_table('dump')
    # ### end Alembic commands ###
