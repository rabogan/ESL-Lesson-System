"""Initial migration

Revision ID: 8cbc940ecfa5
Revises: 
Create Date: 2024-06-01 10:15:51.046713

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8cbc940ecfa5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('lesson_record', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lastEditTime', sa.DateTime(), nullable=True))
        batch_op.drop_column('date')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('lesson_record', schema=None) as batch_op:
        batch_op.add_column(sa.Column('date', sa.DATETIME(), nullable=True))
        batch_op.drop_column('lastEditTime')

    # ### end Alembic commands ###
