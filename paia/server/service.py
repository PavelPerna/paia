import socketserver
import http
import json
import http.server

from paia import PAIALogger,PAIAConfig,PAIAServiceManager

# Server
class PAIAServiceServer(socketserver.ThreadingTCPServer):
    pass

class PAIAServiceHandler(http.server.BaseHTTPRequestHandler):
    ## REST API
    def do_GET(self):
        PAIALogger().debug(f"GET request: {self.path}")
        if self.path == "/services":
            services = PAIAServiceManager().get_services(as_str=True)
            PAIALogger().info(f"Returning services: {services}")
            self.__send_response(200, {"services": services["services"]})
            
        elif self.path == "/config":
            try:
                PAIALogger().info("Returning config")
                self.__send_response(200, PAIAConfig().getConfig())
            except:
                PAIALogger().error(f"Permission denied for config file : {PAIAConfig().config_file}")
                self.__send_error(500, "Permission denied for config file")
        else:
            PAIALogger().warning(f"Unknown path: {self.path}")
            self.__send_error(404, "Not found")
    ## SERVICE API
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            request_data = json.loads(post_data)
            PAIALogger().debug(f"Received POST: {request_data}")

            service_name = request_data.get("service")
            query = request_data.get("query", {})
            stream = request_data.get("stream", False)
            if not service_name:
                PAIALogger().error("Missing service name")
                self.__send_error(400, "Service name is required")
                return
            if not PAIAConfig().getConfig().get("services", {}).get(service_name, {}).get("enabled", True):
                PAIALogger().warning(f"Service disabled: {service_name}")
                self.__send_error(403, f"Service '{service_name}' is disabled")
                return
            service = PAIAServiceManager().get_service(service_name)
            if not service:
                PAIALogger().error(f"Service not found: {service_name}")
                self.__send_error(404, f"Service '{service_name}' not found")
                return
            PAIALogger().info(f"Processing {service_name}, stream={stream}")
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
                        PAIALogger().debug(f"Sending SSE event: {event_data}")
                        self.wfile.write(f"data: {event_data}\n\n".encode('utf-8'))
                        self.wfile.flush()
                except Exception as e:
                    event_data = json.dumps({"error": f"Streaming error: {str(e)}"})
                    PAIALogger().error(f"Streaming error: {event_data}")
                    self.wfile.write(f"data: {event_data}\n\n".encode('utf-8'))
                    self.wfile.flush()
            else:
                PAIALogger().info(f"Non-streaming for: {service_name}")
                for result in service.process(query):
                    self.__send_response(200, result)
                    break
        except json.JSONDecodeError:
            PAIALogger().error("Invalid JSON payload")
            self.__send_error(400, "Invalid JSON payload")
        except Exception as e:
            PAIALogger().error(f"Server error: {str(e)}")
            self.__send_error(500, f"Server error: {str(e)}")

    def do_OPTIONS(self):
        PAIALogger().debug("OPTIONS request")
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
        PAIALogger().debug(f"Sent response: status={status}, data={data}")

    def __send_error(self, status, message):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode('utf-8'))
        PAIALogger().error(f"Sent error: status={status}, message={message}")