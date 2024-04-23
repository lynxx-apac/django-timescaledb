from django.conf import settings
from django.db.backends.postgresql.schema import DatabaseSchemaEditor
from timescale.db.models.fields import TimescaleDateTimeField


class TimescaleBaseSchemaEditor(DatabaseSchemaEditor):
    sql_is_hypertable = """
        SELECT * FROM timescaledb_information.hypertables  
        WHERE hypertable_name = %(table)s%(extra_condition)s
    """
    sql_assert_is_hypertable = f"""
        DO $do$ BEGIN 
        IF EXISTS ({sql_is_hypertable}) THEN NULL; 
        ELSE RAISE EXCEPTION %(error_message)s; 
        END IF;
        END; $do$
    """
    sql_assert_is_not_hypertable = f"""
        DO $do$ BEGIN 
        IF EXISTS ({sql_is_hypertable}) THEN RAISE EXCEPTION %(error_message)s; 
        ELSE NULL; 
        END IF;
        END; $do$
    """
    sql_add_hypertable = """
        SELECT create_hypertable(
        %(table)s, %(partition_column)s, 
        chunk_time_interval => interval %(interval)s, 
        migrate_data => %(migrate)s)
    """
    sql_create_continuous_aggregation = """
        CREATE MATERIALIZED VIEW %(table)s%(columns)s 
        WITH ( timescaledb.continuous %(timescaledb_options)s ) 
        AS %(definition)s 
        %(with_no_data)s 
    """
    sql_add_continuous_aggregate_policy = """
        SELECT add_continuous_aggregate_policy(
            %(table),
            %(start_offset)s
            %(end_offset)s
            %(schedule_interval)s
            %(initial_start)s
            %(timezone)s
            %(if_not_exists)s
        )
    """
    sql_add_retention_policy = """
        SELECT add_retention_policy(
            %(table)s, 
            %(drop_after)s
            %(schedule_interval)s
            %(initial_start)s
            %(timezone)s
            %(if_not_exists)s
            %(drop_created_before)
        )
    """
    sql_remove_retention_policy = (
        ""
    )
    sql_enable_compression = """
        ALTER TABLE %(table)s
        SET (
           timescaledb.compress=%(enable)s
           %(order_by)s
           %(segment_by)s
           %(chunk_time_interval)s
        )
    """
    sql_disable_compression = "ALTER TABLE %(table)s SET (timescaledb.compress=FALSE)"
    sql_add_compression_policy = """
        SELECT add_compression_policy(
            %(table)s, 
            %(compress_after)s
            %(schedule_interval)s
            %(initial_start)s
            %(timezone)s
            %(if_not_exists)s
            %(compress_created_before)
        )
    """
    sql_remove_compression_policy = "SELECT remove_compression_policy(%(table)s%(if_exists)s)"
    sql_decompress_table = "SELECT decompress_chunk(c, true) FROM show_chunks(%(table)s%(older_than)s%(newer_than)s) c"
    sql_disable_scheduled_job = "SELECT alter_job(%(job_id)s, scheduled=FALSE)"
    sql_enable_scheduled_job = "SELECT alter_job(%(job_id)s, scheduled=TRUE)"
    sql_set_chunk_time_interval = "SELECT set_chunk_time_interval(%(table)s, interval %(interval)s)"
    sql_hypertable_is_in_schema = "hypertable_schema = %(schema_name)s"

    def get_hypertable_db_params(self, model):
        return {'table': self.quote_value(model._meta.db_table), 'extra_condition': self._get_extra_condition()}

    def _assert_is_hypertable(self, model):
        """ Assert if the table is a hyper table """
        db_params = self.get_hypertable_db_params(model)
        db_params['error_message'] = self.quote_value(
            f'assert failed - {model._meta.db_table} should be a hyper table')
        sql = self.sql_assert_is_hypertable % db_params
        self.execute(sql)

    def _assert_is_not_hypertable(self, model):
        """ Assert if the table is not a hyper table """
        db_params = self.get_hypertable_db_params(model)
        db_params['error_message'] = self.quote_value(
            f'assert failed - {model._meta.db_table} should not be a hyper table')
        sql = self.sql_assert_is_not_hypertable % db_params
        self.execute(sql)

    def _drop_primary_key(self, model):
        """
        Hypertables can't partition if the primary key is not the partition column.
        So we drop the mandatory primary key django creates.
        """
        sql = self.sql_delete_constraint % {
            'table': self.quote_name(model._meta.db_table), 'name': self.quote_name(f'{model._meta.db_table}_pkey')}
        self.execute(sql)

    def _create_hypertable(self, model, field, should_migrate=False):
        """ Create the hypertable with the partition column being the field. """
        # assert that the table is not already a hypertable
        self._assert_is_not_hypertable(model)
        # drop primary key of the table
        self._drop_primary_key(model)
        db_params = {
            'partition_column': self.quote_value(field.column),
            'interval': self.quote_value(field.interval),
            'table': self.quote_value(model._meta.db_table),
            'migrate': "true" if should_migrate else "false"
        }
        if should_migrate and getattr(settings, "TIMESCALE_MIGRATE_HYPERTABLE_WITH_FRESH_TABLE", False):
            # TODO migrate with fresh table [https://github.com/schlunsen/django-timescaledb/issues/16]
            raise NotImplementedError()
        else:
            sql = self.sql_add_hypertable % db_params
            self.execute(sql)

    def _set_chunk_time_interval(self, model, field):
        """ Change time interval for hypertable """
        # assert if already a hypertable
        self._assert_is_hypertable(model)
        sql = self.sql_set_chunk_time_interval % {
            'table': self.quote_value(model._meta.db_table), 'interval': self.quote_value(field.interval)}
        self.execute(sql)

    def _create_continuous_aggregate(self, model):
        definitions = model.continuous_aggregate.create_materialized_view()
        sql = self.sql_create_continuous_aggregation % {
            'table': self.quote_value(model._meta.db_table), 'definitions': definitions
        }
        self.execute(sql)

    def _enable_compression(self, model):
        sql = self.sql_enable_compression % {
            'table': model._meta.db_table,
            'enable': self.quote_value(model.compression.enable),
            'order_by': self.quote_value(model.compression.order_by),
            'segment_by': self.quote_value(model.compression.segment_by),
            'chunk_time_interval': self.quote_value(model.compression.chunk_time_interval.raw_sql)
        }
        self.execute(sql)

    def _disable_compression(self, model):
        self.execute(self.sql_disable_compression % {'table': model._meta.db_table})

    def _enable_retention(self, model):
        sql = self.sql_add_retention_policy % {
            'table': self.quote_value(model._meta.db_table),
            'drop_after': self.quote_value(model.retention.drop_after),
            'schedule_interval': self.quote_value(model.retention.schedule_interval.raw_sql),
            'initial_start': self.quote_value(model.retention.initial_start),
            'timezone': self.quote_value(model.retention.timezone),
            'if_not_exists': self.quote_value(model.retention.if_not_exists),
            'drop_created_before': self.quote_value(model.retention.drop_created_before)
        }
        self.execute(sql)


    def create_model(self, model):
        """ Find TimescaleDateTimeField in the model and use it as partition when creating hypertable """
        super().create_model(model)
        if getattr(model, 'compression', False):
            self._enable_compression(model)
        if getattr(model, 'continuous_aggregate', False):
            return self._create_continuous_aggregate(model)
        if getattr(model, 'retention', False):
            self._enable_retention(model)
        for field in model._meta.local_fields:
            if isinstance(field, TimescaleDateTimeField):
                self._create_hypertable(model, field)
                break

    def add_field(self, model, field):
        """ When adding field to table if it is TimescaleDateTimeField use it to create hypertable """
        super().add_field(model, field)
        if isinstance(field, TimescaleDateTimeField):
            self._create_hypertable(model, field, True)

    def alter_field(self, model, old_field, new_field, strict=False):
        super().alter_field(model, old_field, new_field, strict)
        if not isinstance(old_field, TimescaleDateTimeField) and isinstance(new_field, TimescaleDateTimeField):
            self._create_hypertable(model, new_field, True)
        elif isinstance(old_field, TimescaleDateTimeField) and isinstance(new_field, TimescaleDateTimeField) \
                and old_field.interval != new_field.interval:
            self._set_chunk_time_interval(model, new_field)

    def _get_extra_condition(self):
        extra_condition = ''
        try:
            if self.connection.schema_name:
                schema = self.sql_hypertable_is_in_schema % {
                    'schema_name': self.quote_value(self.connection.schema_name)}
                extra_condition = f' AND {schema}'
        except Exception as e:
            print(f'{e}. no extra conditions required')
        return extra_condition
