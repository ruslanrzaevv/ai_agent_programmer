from alembic import op
import sqlalchemy as sa

revision = "0004_orbit_fields"
down_revision = "0003_ai_code_fix"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("incidents", sa.Column("orbit_root_cause", sa.Text(), nullable=True))
    op.add_column("incidents", sa.Column("orbit_risk_score", sa.Integer(), nullable=True))
    op.add_column("incidents", sa.Column("orbit_affected_files", sa.JSON(), nullable=True))
    op.add_column("incidents", sa.Column("orbit_affected_services", sa.JSON(), nullable=True))
    op.add_column("incidents", sa.Column("orbit_blast_radius", sa.Integer(), nullable=True))
    op.add_column("incidents", sa.Column("orbit_definitions", sa.JSON(), nullable=True))
    op.add_column("incidents", sa.Column("orbit_imports", sa.JSON(), nullable=True))
    op.add_column("incidents", sa.Column("orbit_calls", sa.JSON(), nullable=True))
    op.add_column("incidents", sa.Column("orbit_dependency_graph", sa.JSON(), nullable=True))
    op.add_column(
    "incidents",
    sa.Column(
        "orbit_error_line",
        sa.Integer(),
        nullable=True,
    )
)


def downgrade():
    op.drop_column("incidents", "orbit_error_line")
    op.drop_column("incidents", "orbit_dependency_graph")
    op.drop_column("incidents", "orbit_calls")
    op.drop_column("incidents", "orbit_imports")
    op.drop_column("incidents", "orbit_definitions")
    op.drop_column("incidents", "orbit_blast_radius")
    op.drop_column("incidents", "orbit_affected_services")
    op.drop_column("incidents", "orbit_affected_files")
    op.drop_column("incidents", "orbit_risk_score")
    op.drop_column("incidents", "orbit_root_cause")