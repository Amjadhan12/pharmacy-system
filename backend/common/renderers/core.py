"""Response renderer that wraps payloads in the standard API envelope.

Envelope format:
    success responses -> {"success": true,  "message": "", "data": ...}
    error responses   -> {"success": false, "message": "...", "errors": {...}}
"""
from rest_framework.renderers import JSONRenderer


class APIRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        response = renderer_context.get("response")

        if isinstance(data, dict) and "success" in data:
            payload = data  # already enveloped (custom view or exception handler)
        elif response is not None and response.status_code >= 400:
            payload = {
                "success": False,
                "message": "Request failed.",
                "errors": data if data is not None else {},
            }
        else:
            payload = {"success": True, "message": "", "data": data}

        return super().render(payload, accepted_media_type, renderer_context)
