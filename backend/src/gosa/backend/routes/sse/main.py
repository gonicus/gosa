from tornado import gen
from gosa.common.gjson import dumps
from gosa.common.sse import EventSource
import random

def event():
    while True:
        yield 'data: ' + dumps(random.sample(range(10000000), 60)) + '\n\n'
        gen.sleep(0.2)

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

class SseHandler(EventSource):

    def initialize(self, source):
        # Ignore 'source'.
        print("SSE Handler initialized")
        super(SseHandler, self).initialize(event())

