# server.py
import http.server
import socketserver
import json
import threading
import socket
import time
import http.client
import argparse
import asyncio

from ai import PAIA_LOGGER,PAIA_CONFIG
from ai.microservice import get_service
from ai.microservice.base_service import PAIA_SERVICE_REGISTRY

class PAIAServer(socketserver.ThreadingTCPServer):
    pass

class PAIAUIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, directory=PAIA_CONFIG.ui_dir)


class PAIAServiceHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        PAIA_LOGGER.debug(f"GET request: {self.path}")
        if self.path == "/services":
            services = list(PAIA_SERVICE_REGISTRY.keys())
            if not services:
                PAIA_LOGGER.error("No services in PAIA_SERVICE_REGISTRY")
                self.__send_error(500, "No services available")
                return
            PAIA_LOGGER.info(f"Returning services: {services}")
            self.__send_response(200, {"services": services})
        elif self.path == "/config":
            try:
                PAIA_LOGGER.info("Returning config")
                self.__send_response(200, PAIA_CONFIG.get())
            except:
                PAIA_LOGGER.error(f"Permission denied for config file : {PAIA_CONFIG.config_path}")
                self.__send_error(500, "Permission denied for config file")
        else:
            PAIA_LOGGER.warning(f"Unknown path: {self.path}")
            self.__send_error(404, "Not found")

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            request_data = json.loads(post_data)
            PAIA_LOGGER.debug(f"Received POST: {request_data}")

            service_name = request_data.get("service")
            query = request_data.get("query", {})
            stream = request_data.get("stream", False)

            if not service_name:
                PAIA_LOGGER.error("Missing service name")
                self.__send_error(400, "Service name is required")
                return

            if not PAIA_CONFIG.get().get("services", {}).get(service_name, {}).get("enabled", True):
                PAIA_LOGGER.warning(f"Service disabled: {service_name}")
                self.__send_error(403, f"Service '{service_name}' is disabled")
                return

            service = get_service(service_name)
            if not service:
                PAIA_LOGGER.error(f"Service not found: {service_name}")
                self.__send_error(404, f"Service '{service_name}' not found")
                return

            PAIA_LOGGER.info(f"Processing {service_name}, stream={stream}")
            if stream:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                try:
                    for result in service.process(query):
                        event_data = json.dumps(result)
                        PAIA_LOGGER.debug(f"Sending SSE event: {event_data}")
                        self.wfile.write(f"data: {event_data}\n\n".encode('utf-8'))
                        self.wfile.flush()
                except Exception as e:
                    event_data = json.dumps({"error": f"Streaming error: {str(e)}"})
                    PAIA_LOGGER.error(f"Streaming error: {event_data}")
                    self.wfile.write(f"data: {event_data}\n\n".encode('utf-8'))
                    self.wfile.flush()
            else:
                PAIA_LOGGER.info(f"Non-streaming for: {service_name}")
                for result in service.process(query):
                    self.__send_response(200, result)
                    break

        except json.JSONDecodeError:
            PAIA_LOGGER.error("Invalid JSON payload")
            self.__send_error(400, "Invalid JSON payload")
        except Exception as e:
            PAIA_LOGGER.error(f"Server error: {str(e)}")
            self.__send_error(500, f"Server error: {str(e)}")

    def do_OPTIONS(self):
        PAIA_LOGGER.debug("OPTIONS request")
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def __send_response(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
        PAIA_LOGGER.debug(f"Sent response: status={status}, data={data}")

    def __send_error(self, status, message):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode('utf-8'))
        PAIA_LOGGER.error(f"Sent error: status={status}, message={message}")


class PAIAApplication:
    def __init__(self):
        parser=argparse.ArgumentParser()
        parser.add_argument("--ui-autostart", choices=['1', 'True', 'true'])
        self.args=parser.parse_args()

    def __getCurrentThread(self):
        return threading.current_thread()
    
    def is_port_in_use(self, host : str, port :int) -> bool:
        try:
            conn = http.client.HTTPConnection(host, port, timeout=1)
            conn.request("HEAD", "/")
            conn.close()
            PAIA_LOGGER.info(f"Port {port} is in use")
            return True
        except (http.client.HTTPException, ConnectionRefusedError, socket.timeout):
            PAIA_LOGGER.info(f"Port {port} is available")
            return False

    def run_server(self, host :str = "localhost", port :int = 8000, server : type = http.server.ThreadingHTTPServer, handler: type = http.server.BaseHTTPRequestHandler, description : str = "Default server" ):
        # Check if available
        if self.is_port_in_use(host,port):
            raise Exception(f"Thread[{self.__getCurrentThread().name}] : [{description}] : Port is in use {host}:{port}")
        # Start 
        with server((host, port), handler) as srv:
            try:
                PAIA_LOGGER.info(f"Thread[{self.__getCurrentThread().name}] : Server[{description}] running at http://{host}:{port}")
                srv.serve_forever()
            except KeyboardInterrupt:
                PAIA_LOGGER.info(f"Thread[{self.__getCurrentThread().name}] : Server[{description}] shutting down at http://{host}:{port}")
                srv.server_close()

    def retry(self, what: callable , retry_count : int = 3, retry_wait : int = 1):
        i = 0
        sanityCheck = 0
        while i < retry_count:
            sanityCheck = sanityCheck + 1
            if(sanityCheck > 100):
                raise Exception('Too many retries')
            try:
                what
                i = retry_count             
                break
            except Exception as e:
                PAIA_LOGGER.info(f"Operation {str(what)} failed with {str(e)}")
                PAIA_LOGGER.info(f"Retry({i}/{retry_count}) - waiting {retry_wait} seconds")
                time.sleep(retry_wait)
            i = i + 1


    def ui_server(self):  
        self.retry(
            what = self.run_server(
                host=PAIA_CONFIG.ui_host,
                port=PAIA_CONFIG.ui_port,
                server=PAIAServer,
                handler=PAIAUIHandler,
                description="UI Server"
            )
        )
    
    def service_server(self):
        self.retry(
            what = self.run_server(
                host=PAIA_CONFIG.host,
                port=PAIA_CONFIG.port,
                server=PAIAServer,
                handler=PAIAServiceHandler,
                description="Main Server"
            )
        )

    def run(self):
        if PAIA_CONFIG.config["ui"]["autostart"]:
            ui_server_thread = threading.Thread(target=self.ui_server,daemon=True,name="UI Server")
            ui_server_thread.start()
        service_server_thread = threading.Thread(target=self.service_server(),daemon=True,name="Service Server")
        service_server_thread.start()
        
if __name__ == "__main__":
    app = PAIAApplication()
    app.run()