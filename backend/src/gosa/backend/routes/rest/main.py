import tornado.web
from gosa.common.gjson import dumps
from gosa.backend.routes.rest.auth import basic_auth

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

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'secret'

@basic_auth(check_auth)
class RestApi(tornado.web.RequestHandler):

    def get(self, path):
        parts = path.split('/')
        root = data["root"]
        
        for part in parts:
            if part == "":
                continue

            if not part in root:
                raise tornado.web.HTTPError(404)
            
            root = root[part]
            
        self.write(dumps(root))
        return
