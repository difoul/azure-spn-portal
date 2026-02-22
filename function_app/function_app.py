import azure.functions as func

from blueprints.health_blueprint import health_bp
from blueprints.owner_blueprint import owner_bp
from blueprints.secret_blueprint import secret_bp
from blueprints.spn_blueprint import spn_bp

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

app.register_functions(health_bp)
app.register_functions(spn_bp)
app.register_functions(secret_bp)
app.register_functions(owner_bp)
