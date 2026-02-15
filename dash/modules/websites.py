import logging
from requests import get


class WebsitesModule:
    def __init__(self, app, route_prefix="/api/websites"):
        self.app = app
        self.route_prefix = route_prefix
        self.app.add_url_rule(self.route_prefix, "websites", self.get_websites)

        self.urls = app.config.get("DASH_URLS", [])

    def get_websites(self):

        if not self.urls:
            return {"error": "No URLs configured"}

        status = {}

        for url in self.urls:
            logging.debug(f"Getting website: {url}")

            response = get(url)
            if response.status_code == 200:
                status[url] = "up"
            else:
                status[url] = "down"

        return status
