import os, sys

# 1) Добавляем корень проекта в PYTHONPATH
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

# 2) Берём Base из того места, где он реально объявлен
from storage.models import Base
# 3) Импортируем сам файл models, чтобы все таблицы зарегистрировались в Base.metadata
import storage.models

from dotenv import load_dotenv
load_dotenv()

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config
db_url = os.getenv("DATABASE_URL")
config.set_main_option("sqlalchemy.url", db_url)

# теперь Base.metadata уже содержит все таблицы из storage.models
target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
