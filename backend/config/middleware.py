"""Request-ID middleware — stamps every request/response with X-Request-ID
and logs one structured line per request for correlation in Sentry/logs."""

import logging
import uuid

logger = logging.getLogger("pyarena.request")


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
        request.request_id = request_id
        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "user_id": getattr(request.user, "id", None),
            },
        )
        return response
