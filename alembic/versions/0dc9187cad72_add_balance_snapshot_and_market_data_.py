"""add_balance_snapshot_and_market_data_tables

Revision ID: 0dc9187cad72
Revises: 811f2e9e8b61
Create Date: 2025-10-29 13:52:01.359360

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0dc9187cad72"
down_revision: Union[str, Sequence[str], None] = "811f2e9e8b61"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create balance_snapshots table
    op.create_table(
        "balance_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exchange_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "free_balance",
            sa.Numeric(precision=20, scale=8),
            nullable=False,
        ),
        sa.Column(
            "locked_balance",
            sa.Numeric(precision=20, scale=8),
            nullable=False,
        ),
        sa.Column(
            "total_balance",
            sa.Numeric(precision=20, scale=8),
            nullable=False,
        ),
        sa.Column(
            "value_in_usd",
            sa.Numeric(precision=20, scale=8),
            nullable=True,
        ),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["exchange_id"],
            ["exchange.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["asset.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "exchange_id",
            "asset_id",
            "snapshot_at",
            name="uq_balance_snapshot_exchange_asset_time",
        ),
    )
    op.create_index(
        op.f("ix_balance_snapshots_exchange_id"),
        "balance_snapshots",
        ["exchange_id"],
    )
    op.create_index(
        op.f("ix_balance_snapshots_asset_id"),
        "balance_snapshots",
        ["asset_id"],
    )
    op.create_index(
        op.f("ix_balance_snapshots_snapshot_at"),
        "balance_snapshots",
        ["snapshot_at"],
    )

    # Create market_data table
    op.create_table(
        "market_data",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trading_pair_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exchange_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timeframe", sa.String(length=10), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("high", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("low", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("close", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("volume", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.ForeignKeyConstraint(
            ["trading_pair_id"],
            ["trading_pair.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["exchange_id"],
            ["exchange.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "trading_pair_id",
            "exchange_id",
            "timeframe",
            "timestamp",
            name="uq_market_data_pair_exchange_timeframe_time",
        ),
    )
    op.create_index(
        op.f("ix_market_data_trading_pair_id"),
        "market_data",
        ["trading_pair_id"],
    )
    op.create_index(op.f("ix_market_data_exchange_id"), "market_data", ["exchange_id"])
    op.create_index(op.f("ix_market_data_timeframe"), "market_data", ["timeframe"])
    op.create_index(op.f("ix_market_data_timestamp"), "market_data", ["timestamp"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_market_data_timestamp"), table_name="market_data")
    op.drop_index(op.f("ix_market_data_timeframe"), table_name="market_data")
    op.drop_index(op.f("ix_market_data_exchange_id"), table_name="market_data")
    op.drop_index(op.f("ix_market_data_trading_pair_id"), table_name="market_data")
    op.drop_table("market_data")

    op.drop_index(
        op.f("ix_balance_snapshots_snapshot_at"), table_name="balance_snapshots"
    )
    op.drop_index(op.f("ix_balance_snapshots_asset_id"), table_name="balance_snapshots")
    op.drop_index(
        op.f("ix_balance_snapshots_exchange_id"),
        table_name="balance_snapshots",
    )
    op.drop_table("balance_snapshots")
