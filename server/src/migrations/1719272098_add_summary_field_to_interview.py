"""Add summary field to Interview

Revision ID: 1719272098
Revises: 1719271831
Create Date: 2024-06-24 23:34:58.984547

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision: str = '1719272098'
down_revision: Union[str, None] = '1719271831'
branch_labels: Union[str, Sequence[str], None] = ()
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('interview', sa.Column('summary', sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column('interview', 'summary')
