import requests


class HomeAssistant:

    def __init__(self, url, token):

        self.url = url.rstrip("/")

        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }


    def get_entities(self):

        r = requests.get(
            self.url + "/api/states",
            headers=self.headers
        )

        r.raise_for_status()

        entities = r.json()


        result = []


        for e in entities:

            domain = e["entity_id"].split(".")[0]


            if domain in allowed:

                result.append(
                    {
                        "id": e["entity_id"],
                        "name": e["attributes"].get(
                            "friendly_name",
                            e["entity_id"]
                        ),
                        "state": e["state"],
                        "domain": domain
                    }
                )


        return result



    def toggle(self, entity_id):

        domain = entity_id.split(".")[0]

        requests.post(
            f"{self.url}/api/services/{domain}/toggle",
            headers=self.headers,
            json={
                "entity_id": entity_id
            }
        )
    
    def get_state(self, entity_id):

        response = requests.get(
            f"{self.url}/api/states/{entity_id}",
            headers=self.headers
        )

        response.raise_for_status()

        return response.json()