from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config


# Create our engine based on the db specified in our config.
APP_ENGINE = create_engine(config.APP_DATABASE)

# Create all tables if they don't exist
config.WBase.metadata.create_all(APP_ENGINE)

# Define our session object which we'll instantiate in other modules.
Session = sessionmaker(APP_ENGINE)