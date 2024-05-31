"""Add lesson_slot_id to LessonRecord

Revision ID: 0219da7e64df
Revises: f3af1f9ece47
Create Date: 2024-05-31 14:23:53.652196

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0219da7e64df'
down_revision = 'f3af1f9ece47'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('lesson_record', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lesson_slot_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_lesson_record_lesson_slot_id', 'lesson_slot', ['lesson_slot_id'], ['id'])


def downgrade():
    with op.batch_alter_table('lesson_record', schema=None) as batch_op:
        batch_op.drop_constraint('fk_lesson_record_lesson_slot_id', type_='foreignkey')
        batch_op.drop_column('lesson_slot_id')
