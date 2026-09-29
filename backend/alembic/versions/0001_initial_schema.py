"""Initial schema setup

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-28 23:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='public'),
        sa.Column('api_key', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_api_key', 'users', ['api_key'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'])

    # Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('user_role', sa.String(length=50), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])

    # Stations
    op.create_table(
        'stations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('elevation_m', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('data_source', sa.String(length=50), nullable=False, server_default='OPENAQ'),
        sa.Column('is_stale', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_sync', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_stations_external_id', 'stations', ['external_id'], unique=True)
    op.create_index('idx_station_coords', 'stations', ['latitude', 'longitude'])

    # Station Readings
    op.create_table(
        'station_readings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('station_id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('parameter', sa.String(length=20), nullable=False, server_default='pm25'),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False, server_default='ug/m3'),
        sa.Column('aqi_value', sa.Integer(), nullable=True),
        sa.Column('aqi_category', sa.String(length=50), nullable=True),
        sa.Column('data_origin', sa.String(length=20), nullable=False, server_default='MEASURED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['station_id'], ['stations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_reading_station_time_param', 'station_readings', ['station_id', 'timestamp', 'parameter'], unique=True)

    # Fire Events
    op.create_table(
        'fire_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('brightness_temp_k', sa.Float(), nullable=True),
        sa.Column('frp_mw', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('acquisition_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('confidence', sa.String(length=20), nullable=True),
        sa.Column('satellite', sa.String(length=50), nullable=False),
        sa.Column('day_night', sa.String(length=5), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_fire_coords_time', 'fire_events', ['latitude', 'longitude', 'acquisition_time'])

    # Weather Snapshots
    op.create_table(
        'weather_snapshots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('temperature_2m_c', sa.Float(), nullable=True),
        sa.Column('relative_humidity_2m_pct', sa.Float(), nullable=True),
        sa.Column('wind_speed_10m_kmh', sa.Float(), nullable=False),
        sa.Column('wind_direction_10m_deg', sa.Float(), nullable=False),
        sa.Column('boundary_layer_height_m', sa.Float(), nullable=True),
        sa.Column('surface_pressure_hpa', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_weather_city_timestamp', 'weather_snapshots', ['city', 'timestamp'], unique=True)

    # Hotspots
    op.create_table(
        'hotspots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('corridor_id', sa.String(length=100), nullable=True),
        sa.Column('centroid_lat', sa.Float(), nullable=False),
        sa.Column('centroid_lon', sa.Float(), nullable=False),
        sa.Column('radius_km', sa.Float(), nullable=False),
        sa.Column('cluster_size', sa.Integer(), nullable=False),
        sa.Column('mean_pm25', sa.Float(), nullable=True),
        sa.Column('max_frp_mw', sa.Float(), nullable=False),
        sa.Column('probable_source', sa.String(length=100), nullable=False),
        sa.Column('reasoning', sa.String(length=500), nullable=False),
        sa.Column('evidence', sa.JSON(), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id')
    )

    # Forecasts
    op.create_table(
        'forecasts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('horizon_hours', sa.Integer(), nullable=False),
        sa.Column('target_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('predicted_pm25', sa.Float(), nullable=True),
        sa.Column('predicted_aqi', sa.Integer(), nullable=True),
        sa.Column('aqi_category', sa.String(length=50), nullable=True),
        sa.Column('lower_bound_pm25', sa.Float(), nullable=True),
        sa.Column('upper_bound_pm25', sa.Float(), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('is_insufficient_data', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Citizen Reports
    op.create_table(
        'citizen_reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('public_id', sa.String(length=20), nullable=False),
        sa.Column('user_session_id', sa.String(length=64), nullable=True),
        sa.Column('raw_lat', sa.Float(), nullable=False),
        sa.Column('raw_lon', sa.Float(), nullable=False),
        sa.Column('public_lat', sa.Float(), nullable=False),
        sa.Column('public_lon', sa.Float(), nullable=False),
        sa.Column('photo_s3_key', sa.String(length=255), nullable=True),
        sa.Column('photo_url', sa.String(length=500), nullable=True),
        sa.Column('user_category', sa.String(length=50), nullable=False),
        sa.Column('user_pm25', sa.Float(), nullable=True),
        sa.Column('gemini_classification', sa.String(length=50), nullable=True),
        sa.Column('gemini_confidence', sa.Float(), nullable=True),
        sa.Column('gemini_rationale', sa.String(length=500), nullable=True),
        sa.Column('is_satellite_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('trust_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('moderated_by', sa.String(length=36), nullable=True),
        sa.Column('moderated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_citizen_reports_public_id', 'citizen_reports', ['public_id'], unique=True)

    # Alerts
    op.create_table(
        'alerts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('corridor_id', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=30), nullable=False),
        sa.Column('title_en', sa.String(length=255), nullable=False),
        sa.Column('title_hi', sa.String(length=255), nullable=False),
        sa.Column('description_en', sa.String(length=1000), nullable=False),
        sa.Column('description_hi', sa.String(length=1000), nullable=False),
        sa.Column('evidence', sa.JSON(), nullable=False),
        sa.Column('rule_trigger', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='NEW'),
        sa.Column('acknowledged_by', sa.String(length=36), nullable=True),
        sa.Column('acknowledged_by_email', sa.String(length=255), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.String(length=36), nullable=True),
        sa.Column('resolved_by_email', sa.String(length=255), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cap_identifier', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alerts_cap_identifier', 'alerts', ['cap_identifier'], unique=True)

    # Model Registry
    op.create_table(
        'model_registry',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('training_window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('training_window_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metrics', sa.JSON(), nullable=False),
        sa.Column('data_hash', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Federated Rounds
    op.create_table(
        'federated_rounds',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('round_number', sa.Integer(), nullable=False),
        sa.Column('coordinator_version', sa.String(length=50), nullable=False),
        sa.Column('participating_nodes', sa.JSON(), nullable=False),
        sa.Column('global_loss', sa.Float(), nullable=False),
        sa.Column('weight_divergence', sa.Float(), nullable=False),
        sa.Column('weights_s3_key', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='COMPLETED'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_federated_rounds_round_number', 'federated_rounds', ['round_number'], unique=True)


def downgrade() -> None:
    op.drop_table('federated_rounds')
    op.drop_table('model_registry')
    op.drop_table('alerts')
    op.drop_table('citizen_reports')
    op.drop_table('forecasts')
    op.drop_table('hotspots')
    op.drop_table('weather_snapshots')
    op.drop_table('fire_events')
    op.drop_table('station_readings')
    op.drop_table('stations')
    op.drop_table('audit_logs')
    op.drop_table('users')
