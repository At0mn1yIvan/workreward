import json

from rest_framework.renderers import JSONRenderer


class BaseJSONRenderer(JSONRenderer):
    charset = "utf-8"
    root_key = "data"

    def render(self, data, media_type=None, renderer_context=None) -> str:
        return json.dumps({self.root_key: data})
