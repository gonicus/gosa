from gosa.common.sse import EventSource
from tornado import web
import random

class SseClient(web.RequestHandler):
    def get(self):
        debug_template = """
                <html>
                   <head>
                   </head>
                   <body>
                     <h1>Server sent events</h1>
                     <div id="event"></div>
                     <script type="text/javascript">

                     var eventOutputContainer = document.getElementById("event");
                     var evtSrc = new EventSource("/events");

                     evtSrc.onmessage = function(e) {
                         eventOutputContainer.innerHTML = e.data;
                     };

                     </script>
                   </body>
                 </html>
                """
        self.write(debug_template)


class SseHandler(EventSource):

    def post(self):
        self.source.data = str(self.request.body)
