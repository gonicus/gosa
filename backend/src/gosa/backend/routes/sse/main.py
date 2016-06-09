from flask import Flask, Response, json
from flask.views import MethodView
import random
import gevent

app = Flask(__name__)


def event():
    while True:
        yield 'data: ' + json.dumps(random.sample(range(10000000), 60)) + '\n\n'
        gevent.sleep(0.2)

# Client code consumes like this.
# @app.route("/")
# def index():
#     debug_template = """
#         <html>
#            <head>
#            </head>
#            <body>
#              <h1>Server sent events</h1>
#              <div id="event"></div>
#              <script type="text/javascript">
#
#              var eventOutputContainer = document.getElementById("event");
#              var evtSrc = new EventSource("/subscribe");
#
#              evtSrc.onmessage = function(e) {
#                  console.log(e.data);
#                  eventOutputContainer.innerHTML = e.data;
#              };
#
#              </script>
#            </body>
#          </html>
#         """
#     return (debug_template)

class SseHandler(MethodView):

    def get(self):
        return Response(event(), mimetype="text/event-stream")