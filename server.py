# server.py
import http.server
import socketserver
import json
import threading
import socket
import time
import http.client

from ai.config import PAIAConfig
from ai.logger import PAIALogger
from ai.microservice import get_service
from ai.microservice.base_service import SERVICE_REGISTRY


logger = PAIALogger().get()
config = PAIAConfig()

class AIMicroServiceHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        logger.debug(f"GET request: {self.path}")
        if self.path == "/services":
            services = list(SERVICE_REGISTRY.keys())
            if not services:
                logger.error("No services in SERVICE_REGISTRY")
                self._send_error(500, "No services available")
                return
            logger.info(f"Returning services: {services}")
            self._send_response(200, {"services": services})
        elif self.path == "/config":
            try:
                logger.info("Returning config")
                self._send_response(200, config.get())
            except:
                logger.error(f"Permission denied for config file : {config.config_path}")
                self._send_error(500, "Permission denied for config file")
        else:
            logger.warning(f"Unknown path: {self.path}")
            self._send_error(404, "Not found")

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            request_data = json.loads(post_data)
            logger.debug(f"Received POST: {request_data}")

            service_name = request_data.get("service")
            query = request_data.get("query", {})
            stream = request_data.get("stream", False)

            if not service_name:
                logger.error("Missing service name")
                self._send_error(400, "Service name is required")
                return

            if not config.get().get("services", {}).get(service_name, {}).get("enabled", True):
                logger.warning(f"Service disabled: {service_name}")
                self._send_error(403, f"Service '{service_name}' is disabled")
                return

            service = get_service(service_name)
            if not service:
                logger.error(f"Service not found: {service_name}")
                self._send_error(404, f"Service '{service_name}' not found")
                return

            logger.info(f"Processing {service_name}, stream={stream}")
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
                        logger.debug(f"Sending SSE event: {event_data}")
                        self.wfile.write(f"data: {event_data}\n\n".encode('utf-8'))
                        self.wfile.flush()
                except Exception as e:
                    event_data = json.dumps({"error": f"Streaming error: {str(e)}"})
                    logger.error(f"Streaming error: {event_data}")
                    self.wfile.write(f"data: {event_data}\n\n".encode('utf-8'))
                    self.wfile.flush()
            else:
                logger.info(f"Non-streaming for: {service_name}")
                for result in service.process(query):
                    self._send_response(200, result)
                    break

        except json.JSONDecodeError:
            logger.error("Invalid JSON payload")
            self._send_error(400, "Invalid JSON payload")
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
            self._send_error(500, f"Server error: {str(e)}")

    def _send_response(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
        logger.debug(f"Sent response: status={status}, data={data}")

    def _send_error(self, status, message):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode('utf-8'))
        logger.error(f"Sent error: status={status}, message={message}")

    def do_OPTIONS(self):
        logger.debug("OPTIONS request")
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

def is_port_in_use(host, port):
    try:
        conn = http.client.HTTPConnection(host, port, timeout=1)
        conn.request("HEAD", "/")
        conn.close()
        logger.info(f"Port {port} is in use")
        return True
    except (http.client.HTTPException, ConnectionRefusedError, socket.timeout):
        logger.info(f"Port {port} is available")
        return False

def start_ui_server():
    config = PAIAConfig()
    handler = http.server.SimpleHTTPRequestHandler
    handler.directory = config.ui_dir
    with socketserver.TCPServer(("", 8080), handler) as httpd:
        logger.info("UI server running at http://localhost:8080")
        httpd.serve_forever()

def run_server():
    if not is_port_in_use("localhost", 8080):
        logger.info("Starting UI server in separate thread")
        ui_thread = threading.Thread(target=start_ui_server, daemon=True)
        ui_thread.start()
        time.sleep(1)
    else:
        logger.info("UI server already running on port 8080")

    server_address = (config.host, config.port)
    with socketserver.ThreadingTCPServer(server_address, AIMicroServiceHandler) as httpd:
        logger.info(f"Main server running at http://{config.host}:{config.port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
            httpd.server_close()

if __name__ == "__main__":
    run_server()