from alembic import context

from backend.main import engine, schema

if context.is_offline_mode():
    context.configure(url=str(engine.url), target_metadata=schema, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=schema)
        with context.begin_transaction():
            context.run_migrations()
