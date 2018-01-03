from gosa.common.hsts_request_handler import HSTSRequestHandler


class State:
    system_state = "initializing"


class SystemStateReporter(HSTSRequestHandler):
    """
    Return the current system state
    """
    _xsrf = None

    # disable xsrf feature
    def check_xsrf_cookie(self):
        pass

    def get(self, path):
        return State.system_state
