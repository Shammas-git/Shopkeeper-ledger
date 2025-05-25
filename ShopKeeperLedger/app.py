import os  # Used to access environment variables
import logging  # Used for application logging and debugging

# Flask framework imports
from flask import Flask  # The core Flask framework
from flask_sqlalchemy import SQLAlchemy  # Database ORM for Flask
from sqlalchemy.orm import DeclarativeBase  # Base class for database models
from werkzeug.middleware.proxy_fix import ProxyFix  # Fixes URLs behind proxies
from flask_login import LoginManager  # Handles user authentication


# Configure application logging - helps with debugging
logging.basicConfig(level=logging.DEBUG)  # Set logging level to DEBUG for detailed logs

class Base(DeclarativeBase):
    """
    Base class for all database models.
    
    This class is used by SQLAlchemy to create the database schema.
    It doesn't need any content because it inherits everything from DeclarativeBase.
    """
    pass


# Create SQLAlchemy database instance with our Base class
db = SQLAlchemy(model_class=Base)

# Create the Flask application instance
app = Flask(__name__)

# Set secret key from environment variables - used for session security
app.secret_key = os.environ.get("SESSION_SECRET")

# Fix URLs when running behind a proxy (necessary for proper URL generation)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure database connection using environment variable
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")

# Set database connection options for better performance and reliability
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,  # Reconnect to database server every 5 minutes
    "pool_pre_ping": True,  # Check connection before using it
}

# No external authentication providers are used in this application
# We only use internal username/password authentication
    
# Connect the database to our Flask app
db.init_app(app)

# Set up user authentication with Flask-Login
login_manager = LoginManager()  # Create login manager instance
login_manager.init_app(app)  # Connect login manager to our Flask app
login_manager.login_view = 'routes.login'  # Specify the login page route

# This context is used for database setup and route registration
with app.app_context():
    # Import the models so SQLAlchemy knows about them
    import models  # noqa: F401
    
    # Create all database tables if they don't exist yet
    db.create_all()

    # Import and register routes blueprint to organize application routes
    from routes import routes
    
    app.register_blueprint(routes)
    
    # Set up user loader function for Flask-Login
    from models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        """
        This function tells Flask-Login how to find a specific user.
        
        When a user is logged in, Flask-Login needs to know how to 
        retrieve that user from the database using their ID.
        
        Args:
            user_id (str): The ID of the user to load (as a string)
            
        Returns:
            User: The user object if found, or None if not found
        """
        return User.query.get(int(user_id))  # Convert string ID to integer and find user
