from alembic import op
import sqlalchemy as sa

revision = "0002_telegram"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("telegram_chat_id", sa.BigInteger(), nullable=True))
    op.add_column("users", sa.Column("telegram_username", sa.String(128), nullable=True))
    op.add_column("users", sa.Column("telegram_link_token", sa.String(64), nullable=True))

    op.create_unique_constraint("uq_users_telegram_chat_id", "users", ["telegram_chat_id"])
    op.create_unique_constraint("uq_users_telegram_link_token", "users", ["telegram_link_token"])

    # Добавляем telegram в enum notificationchannel
    op.execute("ALTER TYPE notificationchannel ADD VALUE IF NOT EXISTS 'telegram'")


def downgrade() -> None:
    op.drop_constraint("uq_users_telegram_chat_id", "users")
    op.drop_constraint("uq_users_telegram_link_token", "users")
    op.drop_column("users", "telegram_chat_id")
    op.drop_column("users", "telegram_username")
    op.drop_column("users", "telegram_link_token")