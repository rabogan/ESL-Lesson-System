"""Add timezone to Student Model

Revision ID: f3af1f9ece47
Revises: 53667a642fb7
Create Date: 2024-05-31 01:52:38.649190

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3af1f9ece47'
down_revision = '53667a642fb7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('student', schema=None) as batch_op:
        batch_op.add_column(sa.Column('timezone', sa.String(length=50), nullable=True))

    with op.batch_alter_table('teacher', schema=None) as batch_op:
        batch_op.add_column(sa.Column('timezone', sa.String(length=50), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('teacher', schema=None) as batch_op:
        batch_op.drop_column('timezone')

    with op.batch_alter_table('student', schema=None) as batch_op:
        batch_op.drop_column('timezone')

    # ### end Alembic commands ###