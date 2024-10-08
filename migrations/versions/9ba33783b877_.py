"""empty message

Revision ID: 9ba33783b877
Revises: 41eb15d37c84
Create Date: 2024-07-26 10:33:31.112172

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9ba33783b877'
down_revision = '41eb15d37c84'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # these are auto added by postgres, but added to this file so they will not be added again.
    # with op.batch_alter_table('connection_database_type', schema=None) as batch_op:
    #     batch_op.create_index(batch_op.f('ix_connection_database_type_id'), ['id'], unique=False)

    with op.batch_alter_table('login', schema=None) as batch_op:
        batch_op.alter_column('login_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False,
               existing_server_default=sa.text('now()'))

    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.alter_column('created',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False,
               existing_server_default=sa.text('now()'))

    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.alter_column('created',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False,
               existing_server_default=sa.text('now()'))
        batch_op.drop_index('ix_task_email_error')

    # these are auto added by postgres, but added to this file so they will not be added again.
    # with op.batch_alter_table('task_destination_file_type', schema=None) as batch_op:
    #    batch_op.create_index(batch_op.f('ix_task_destination_file_type_id'), ['id'], unique=False)

    
    # these are auto added by postgres, but added to this file so they will not be added again.
    # with op.batch_alter_table('task_processing_type', schema=None) as batch_op:
    #    batch_op.create_index(batch_op.f('ix_task_processing_type_id'), ['id'], unique=False)

    # with op.batch_alter_table('task_status', schema=None) as batch_op:
    #    batch_op.create_index(batch_op.f('ix_task_status_id'), ['id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('task_status', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_task_status_id'))

    with op.batch_alter_table('task_processing_type', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_task_processing_type_id'))


    with op.batch_alter_table('task_destination_file_type', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_task_destination_file_type_id'))

    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.create_index('ix_task_email_error', ['email_error'], unique=False)
        batch_op.alter_column('created',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('now()'))

    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.alter_column('created',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('now()'))

    with op.batch_alter_table('login', schema=None) as batch_op:
        batch_op.alter_column('login_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('now()'))

    with op.batch_alter_table('connection_database_type', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_connection_database_type_id'))

    # ### end Alembic commands ###
