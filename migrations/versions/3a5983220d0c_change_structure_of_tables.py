"""Change Structure Of Tables

Revision ID: 3a5983220d0c
Revises: 
Create Date: 2024-06-07 11:57:43.051964

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a5983220d0c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('lesson_record', schema=None) as batch_op:
        batch_op.drop_column('new_phrases')
        batch_op.drop_column('new_words')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('lesson_record', schema=None) as batch_op:
        batch_op.add_column(sa.Column('new_words', sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column('new_phrases', sa.TEXT(), nullable=True))

    # ### end Alembic commands ###