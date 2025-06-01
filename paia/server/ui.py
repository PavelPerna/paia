# UI Server
import socketserver
import http

from paia import PAIAConfig

class PAIAUIServer(socketserver.ThreadingTCPServer):
    pass

class PAIAUIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, directory=PAIAConfig().ui_dir)
