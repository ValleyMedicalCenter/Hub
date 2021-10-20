"""empty message

Revision ID: 882dc38883bf
Revises: 93ae809498a6
Create Date: 2020-09-25 14:34:40.776795

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "882dc38883bf"
down_revision = "93ae809498a6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "task", sa.Column("source_query_include_header", sa.Integer(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("task", "source_query_include_header")
    # ### end Alembic commands ###
