import sqlite3
import psycopg

import click
from flask import current_app, g

def get_db():
    if 'db' not in g:
        match current_app.config["DB_TYPE"]:
            case "pg":
                dblib = psycopg
            case "sqlite":
                dblib = sqlite3
            case _:
                dblib = sqlite3
        db = dblib.connect(
            current_app.config['DATABASE'], row_factory=psycopg.rows.dict_row
            # detect_types=dblib.PARSE_DECLTYPES
        )
        db.autocommit = True
        # g.db.row_factory = dblib.Row
        if (db.execute("SELECT * FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';").rowcount == 0):
            with current_app.open_resource('schema.sql') as f:
                db.execute(f.read().decode('utf8'))
        g.db = db
    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

# run "flask init-db"
@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)