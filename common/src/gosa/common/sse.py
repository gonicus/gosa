from gosa.common.gjson import dumps
from tornado import web, gen
from tornado.iostream import StreamClosedError

class DataSource(object):
    """Generic object for producing data to feed to clients."""

    def __init__(self, initial_data=None):
        self._data = initial_data

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, new_data):
        self._data = new_data

class EventSource(web.RequestHandler):

    """Basic handler for server-sent events."""
    def initialize(self, source=None):
        """The ``source`` parameter is a string that is updated with
        new data. The :class:`EventSouce` instance will continuously
        check if it is updated and publish to clients when it is.
        """
        self.source = source or DataSource()
        self._last = None
        self.set_header('Content-Type', 'text/event-stream; charset=utf-8')
        self.set_header('Cache-Control', 'no-cache')
        self.set_header('Connection','keep-alive')

    @gen.coroutine
    def publish(self, data, event=None):
        """
        Actually emits the data to the waiting JS
        """
        response = u''
        encoded_data = dumps(data)
        if event != None:
            response += u'event: ' + str(event).strip() + u'\n'

        response += u'data: ' + encoded_data.strip() + u'\n\n'
        try:
            self.write(response)
            yield self.flush()
        except StreamClosedError:
            pass

    @gen.coroutine
    def get(self):
        while True:
            newData = self.source.data
            if (newData):
                print(newData)
            if newData != self._last:
                yield self.publish(newData)
                self._last = newData
            else:
                yield gen.sleep(0.005)