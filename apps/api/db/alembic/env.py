import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config

from db.base import metadata
from db.models import define_tables


config = context.config
config.set_main_option("sqlalchemy.url", os.getenv("APP_DATABASE_URL", config.get_main_option("sqlalchemy.url") or ""))
if config.config_file_name:
    fileConfig(config.config_file_name)

define_tables(metadata)
target_metadata = metadata


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    connectable = async_engine_from_config(config.get_section(config.config_ini_section) or {}, prefix="sqlalchemy.", pool_pre_ping=True)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_offline():
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
