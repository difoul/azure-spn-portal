import json

import azure.functions as func

health_bp = func.Blueprint()


@health_bp.function_name("HealthCheck")
@health_bp.route(route="v1/health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
async def health_check(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps({"status": "ok"}),
        status_code=200,
        mimetype="application/json",
    )
