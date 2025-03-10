"""empty message

Revision ID: 710037cf9869
Revises: f0fbbdd45fa1
Create Date: 2025-03-09 22:11:41.416233

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '710037cf9869'
down_revision = 'f0fbbdd45fa1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('managers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('username', sa.String(length=255), nullable=False))
        batch_op.create_unique_constraint(None, ['username'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('managers', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_column('username')

    # ### end Alembic commands ###
