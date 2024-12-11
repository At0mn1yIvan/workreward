import json

from rest_framework.renderers import JSONRenderer


class TaskJSONRenderer(JSONRenderer):
    charset = "utf-8"

    def render(self, data, media_type=None, renderer_context=None) -> str:
        return json.dumps({"task": data})
