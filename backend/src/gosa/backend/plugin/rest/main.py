from flask import abort, jsonify
from flask.views import MethodView
from gosa.backend.plugin.rest.auth import *

data = {
    "root": {
        "o": "GONICUS GmbH",
        "Testabteilung1": {
            "description": "Dies ist ein Test Text",
            "manager": "sepp",
            "user": {
                "testuser1": {
                    "userPassword": "xxxxxx",
                    "gender": "m",
                    "dateOfBirth": "1989-04-29"
                },
                "sepp": {
                    "customAttr": "foobar"
                }
            },
            "group": {
                "chefs": []
            }
        },
        "Testabteilung": {
            "description": "Doppelt gemoppelt",
            "manager": "sepp",
            "group": {
                "chefs": {
                    "gidNumber": 9923
                }
            }
        }
    }
}

class RestApi(MethodView):
    decorators = [requires_auth]
    
    def get(self, path):
        parts = path.split('/')
        root = data["root"]
        
        for part in parts:
            if part == "":
                continue

            if not part in root:
                abort(404)
            
            root = root[part]
            
        return jsonify(root)
