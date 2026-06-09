from alembic import op
import sqlalchemy as sa

revision = "0003_ai_code_fix"
down_revision = "0002_telegram"


def upgrade():
    op.add_column(
        "incidents",
        sa.Column("ai_fix_file", sa.Text(), nullable=True),
    )

    op.add_column(
        "incidents",
        sa.Column("ai_fix_old_code", sa.Text(), nullable=True),
    )

    op.add_column(
        "incidents",
        sa.Column("ai_fix_new_code", sa.Text(), nullable=True),
    )

    op.add_column(
        "incidents",
        sa.Column("ai_merge_request_url", sa.Text(), nullable=True),
    )


def downgrade():
    op.drop_column("incidents", "ai_merge_request_url")
    op.drop_column("incidents", "ai_fix_new_code")
    op.drop_column("incidents", "ai_fix_old_code")
    op.drop_column("incidents", "ai_fix_file")