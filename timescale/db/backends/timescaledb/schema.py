from django.conf import settings
from django.db.backends.postgresql.schema import DatabaseSchemaEditor
from timescale.db.models.fields import TimescaleDateTimeField


class TimescaleBaseSchemaEditor(DatabaseSchemaEditor):
    sql_is_hypertable = (
        "SELECT * FROM timescaledb_information.hypertables " 
        "WHERE hypertable_name = %(table)s%(extra_condition)s"
    )
    sql_assert_is_hypertable = (
        f"DO $do$ BEGIN "
        "IF EXISTS (" + sql_is_hypertable + ") THEN NULL; "
        "ELSE RAISE EXCEPTION %(error_message)s; "
        "END IF;"
        "END; $do$"
    )
    sql_assert_is_not_hypertable = (
        "DO $do$ BEGIN "
        "IF EXISTS (" + sql_is_hypertable + ") THEN RAISE EXCEPTION %(error_message)s; "
        "ELSE NULL; "
        "END IF;"
        "END; $do$"
    )
    sql_add_hypertable = (
        "SELECT create_hypertable("
        "%(table)s, %(partition_column)s, "
        "chunk_time_interval => interval %(interval)s, "
        "migrate_data => %(migrate)s)"
    )
    sql_create_continuous_aggregation = (
        "CREATE MATERIALIZED VIEW %(table)s%(columns)s "
        "WITH ( timescaledb.continuous %(timescaledb_options)s ) "
        "AS %(definition)s "
        "%(with_no_data)s "
    )
    sql_create_timescaledb_policy = (
        ""
    )
    sql_set_chunk_time_interval = "SELECT set_chunk_time_interval(%(table)s, interval %(interval)s)"
    sql_hypertable_is_in_schema = "hypertable_schema = %(schema_name)s"

    @staticmethod
    def table_name(model):
        return model._meta.db_table

    def get_hypertable_db_params(self, model):
        return {'table': self.quote_value(self.table_name(model)), 'extra_condition': self._get_extra_condition()}

    def _assert_is_hypertable(self, model):
        """ Assert if the table is a hyper table """
        db_params = self.get_hypertable_db_params(model)
        db_params['error_message'] = self.quote_value(
            f'assert failed - {self.table_name(model)} should be a hyper table')
        sql = self.sql_assert_is_hypertable % db_params
        self.execute(sql)

    def _assert_is_not_hypertable(self, model):
        """ Assert if the table is not a hyper table """
        db_params = self.get_hypertable_db_params(model)
        db_params['error_message'] = self.quote_value(
            f'assert failed - {self.table_name(model)} should not be a hyper table')
        sql = self.sql_assert_is_not_hypertable % db_params
        self.execute(sql)

    def _drop_primary_key(self, model):
        """
        Hypertables can't partition if the primary key is not
        the partition column.
        So we drop the mandatory primary key django creates.
        """
        sql = self.sql_delete_constraint % {
            'table': self.quote_name(self.table_name(model)), 'name': self.quote_name(f'{self.table_name(model)}_pkey')}
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
            'table': self.quote_value(self.table_name(model)),
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
            'table': self.quote_value(self.table_name(model)), 'interval': self.quote_value(field.interval)}
        self.execute(sql)

    def create_model(self, model):
        """ Find TimescaleDateTimeField in the model and use it as partition when creating hypertable """
        super().create_model(model)
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
