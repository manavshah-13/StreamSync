"""init_streamsync_analytical_layers

Revision ID: 8fa2c6d48a1b
Revises: 
Create Date: 2026-06-14 06:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8fa2c6d48a1b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create experiments table
    op.create_table(
        'experiments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('variant_a_config', sa.JSON(), nullable=False),
        sa.Column('variant_b_config', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_experiments_created_at', 'experiments', ['created_at'], unique=False)
    op.create_index('ix_experiments_name', 'experiments', ['name'], unique=True)

    # 2. Create experiment_results table
    op.create_table(
        'experiment_results',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('variant_group', sa.String(), nullable=False),
        sa.Column('conversions', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('total_revenue', sa.Numeric(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_experiment_results_experiment_id', 'experiment_results', ['experiment_id'], unique=False)
    op.create_index('ix_experiment_results_updated_at', 'experiment_results', ['updated_at'], unique=False)

    # 3. Create fairness_logs table
    op.create_table(
        'fairness_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('metric_scanned', sa.String(), nullable=False),
        sa.Column('bias_detected', sa.Boolean(), nullable=False),
        sa.Column('variance_score', sa.Float(), nullable=False),
        sa.Column('operational_fix', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_fairness_logs_timestamp', 'fairness_logs', ['timestamp'], unique=False)

    # 4. Create pricing_history table
    op.create_table(
        'pricing_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.String(), nullable=False),
        sa.Column('old_price', sa.Numeric(), nullable=False),
        sa.Column('new_price', sa.Numeric(), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pricing_history_product_id', 'pricing_history', ['product_id'], unique=False)
    op.create_index('ix_pricing_history_timestamp', 'pricing_history', ['timestamp'], unique=False)

    # 5. Create onboarding_preferences table
    op.create_table(
        'onboarding_preferences',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('gender', sa.String(), nullable=True),
        sa.Column('age_group', sa.String(), nullable=True),
        sa.Column('interests', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('shopping_preferences', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_onboarding_preferences_user_id', 'onboarding_preferences', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_onboarding_preferences_user_id', table_name='onboarding_preferences')
    op.drop_table('onboarding_preferences')

    op.drop_index('ix_pricing_history_timestamp', table_name='pricing_history')
    op.drop_index('ix_pricing_history_product_id', table_name='pricing_history')
    op.drop_table('pricing_history')

    op.drop_index('ix_fairness_logs_timestamp', table_name='fairness_logs')
    op.drop_table('fairness_logs')

    op.drop_index('ix_experiment_results_updated_at', table_name='experiment_results')
    op.drop_index('ix_experiment_results_experiment_id', table_name='experiment_results')
    op.drop_table('experiment_results')

    op.drop_index('ix_experiments_name', table_name='experiments')
    op.drop_index('ix_experiments_created_at', table_name='experiments')
    op.drop_table('experiments')
