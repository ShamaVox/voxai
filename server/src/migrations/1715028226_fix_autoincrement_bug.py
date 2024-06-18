"""Fix autoincrement bug

Revision ID: 1715028226
Revises: 1714683528
Create Date: 2024-05-06 20:43:46.522709

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision: str = '1715028226'
down_revision: Union[str, None] = '1714683528'
branch_labels: Union[str, Sequence[str], None] = ()
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Create sequences if they don't exist
    op.execute("CREATE SEQUENCE IF NOT EXISTS account_account_id_seq")
    op.execute("CREATE SEQUENCE IF NOT EXISTS metric_history_id_seq")
    op.execute("CREATE SEQUENCE IF NOT EXISTS skill_skill_id_seq")

    # Set default values for the columns using the sequences
    op.execute("ALTER TABLE account ALTER COLUMN account_id SET DEFAULT nextval('account_account_id_seq')")
    op.execute("ALTER TABLE metric_history ALTER COLUMN id SET DEFAULT nextval('metric_history_id_seq')")
    op.execute("ALTER TABLE skill ALTER COLUMN skill_id SET DEFAULT nextval('skill_skill_id_seq')")

    # Associate the sequences with the respective columns
    op.execute("ALTER SEQUENCE account_account_id_seq OWNED BY account.account_id")
    op.execute("ALTER SEQUENCE metric_history_id_seq OWNED BY metric_history.id")
    op.execute("ALTER SEQUENCE skill_skill_id_seq OWNED BY skill.skill_id")


def downgrade():
    # Disassociate the sequences from the respective columns
    op.execute("ALTER SEQUENCE account_account_id_seq OWNED BY NONE")
    op.execute("ALTER SEQUENCE metric_history_id_seq OWNED BY NONE")
    op.execute("ALTER SEQUENCE skill_skill_id_seq OWNED BY NONE")

    # Remove the default values from the columns
    op.execute("ALTER TABLE account ALTER COLUMN account_id DROP DEFAULT")
    op.execute("ALTER TABLE metric_history ALTER COLUMN id DROP DEFAULT")
    op.execute("ALTER TABLE skill ALTER COLUMN skill_id DROP DEFAULT")

    # Drop the sequences
    op.execute("DROP SEQUENCE IF EXISTS account_account_id_seq")
    op.execute("DROP SEQUENCE IF EXISTS metric_history_id_seq")
    op.execute("DROP SEQUENCE IF EXISTS skill_skill_id_seq")
