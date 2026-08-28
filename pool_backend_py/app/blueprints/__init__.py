from app.blueprints.addresses import bp as addresses_bp
from app.blueprints.crews import bp as crews_bp
from app.blueprints.health import bp as health_bp
from app.blueprints.organisations import bp as organisations_bp
from app.blueprints.roles import bp as roles_bp
from app.blueprints.users import bp as users_bp


def register_blueprints(app):
    app.register_blueprint(health_bp)
    app.register_blueprint(organisations_bp)
    app.register_blueprint(crews_bp)
    app.register_blueprint(addresses_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(roles_bp)
