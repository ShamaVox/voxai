from .app import app as app
from . import database
from flask_alembic import Alembic
from os import environ

# Alembic setup      

if 'ALEMBIC' in environ:
    with app.app_context():
        alembic = Alembic(app)
        if environ['ALEMBIC'] == "upgrade":
            input("Press enter to start upgrade migration")
            alembic.upgrade()
        elif environ['ALEMBIC'] == "downgrade":
            input("Press enter to start upgrade migration")
            alembic.upgrade()
        elif environ['ALEMBIC'] == "migrate":
            migration_message = input("Migration message: ")
            alembic.revision(message=migration_message)
            input("Press enter to apply new upgrade migration. You may want to make some changes first.")
            alembic.upgrade()
        else:
            print("Invalid ALEMBIC environment variable: ", environ['ALEMBIC'])