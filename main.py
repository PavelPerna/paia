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

from ai import PAIAConfig,PAIALogger
from ai.microservice import get_service
from ai.microservice.base_service import PAIA_SERVICE_REGISTRY

class PAIAServer(socketserver.ThreadingTCPServer):
    pass

class PAIAUIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, directory=PAIAConfig().ui_dir)



class PAIAServiceHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        PAIALogger().debug(f"GET request: {self.path}")
        if self.path == "/services":
            services = list(PAIA_SERVICE_REGISTRY.keys())
            if not services:
                PAIALogger().error("No services in PAIA_SERVICE_REGISTRY")
                self.__send_error(500, "No services available")
                return
            PAIALogger().info(f"Returning services: {services}")
            self.__send_response(200, {"services": services})
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

            service = get_service(service_name)
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

class PAIAApplication:
    def __init__(self):
        PAIALogger().info("PAIAApplication Start")
        self.servers = []
        parser=argparse.ArgumentParser()
        parser.add_argument("--ui-autostart",required=False, choices=[True,False], dest='ui_autostart', type=bool, help='Automatically start User interface service')
        self.args=parser.parse_args()
        
    def __getCurrentThread(self):
        return threading.current_thread()
        
    def port_available(self, ip : str, port : int) -> bool:
        res = False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP
            #sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            sock.settimeout(2)
            result = sock.connect_ex((ip,port))
            PAIALogger().debug(f"Port test: {result}")       
            if result == 0:
                PAIALogger().debug(f"Port is open")            
                res = True
            sock.close()
        except Exception as e:
            PAIALogger().debug(f"{str(e)}")
            res = True 
        return res
            
    def run_server(self, host :str = "localhost", port :int = 8000, server : type = http.server.ThreadingHTTPServer, handler: type = http.server.BaseHTTPRequestHandler, description : str = "Default server" ,retry_count :int = 3,retry_wait : int = 1):
        # Check if available
        ok = False
        retry_count_current = 0
        retry_str = ""
        while retry_count_current < retry_count and not ok:
            retry_count_current = retry_count_current + 1
            retry_str = f"Retry ({retry_count_current})" if retry_count_current > 0 else ""
            if not self.port_available(host, port):
                PAIALogger().info(f"Thread[{self.__getCurrentThread().name}] Run server - [{description}] : Port is in use {host}:{port} {retry_str}")
            else:
                PAIALogger().info(f"Thread[{self.__getCurrentThread().name}] Run server - [{description}] : Port free {host}:{port} {retry_str}")
                
            # Start 
            try:
                with server((host, port), handler) as srv:
                    if not srv in self.servers:
                        self.servers.append(srv)
                    PAIALogger().info(f"Thread[{self.__getCurrentThread().name}] : Run server - Server[{description}] running at http://{host}:{port}")
                    ok = True
                    srv.serve_forever()    
            except:
                ok = False        

            time.sleep(retry_wait)

        if not ok:
            PAIALogger().info(f"Thread[{self.__getCurrentThread().name}] Run server - [{description}] : {host}:{port} {retry_str}   - FAILED!!!")
            


    def ui_server(self):  
        self.run_server(
                host=PAIAConfig().ui_host,
                port=PAIAConfig().ui_port,
                server=PAIAServer,
                handler=PAIAUIHandler,
                description="UI Server",
                retry_count=10,
                retry_wait=1
        )
 
    
    def service_server(self):
        self.run_server(
            host=PAIAConfig().host,
            port=PAIAConfig().port,
            server=PAIAServer,
            handler=PAIAServiceHandler,
            description="Service Server",
                retry_count=10,
                retry_wait=1
        )

    def run(self):
        if PAIAConfig().getConfig().get("ui",{}).get("autostart",True):
            self.ui_server_thread = threading.Thread(target=self.ui_server,daemon=True, name="UI Thread",)
            self.ui_server_thread.start()
        self.service_server_thread = threading.Thread(target=self.service_server,daemon=True,name="Service Thread")
        self.service_server_thread.start()
        while True:
            time.sleep(1)
    
    def __del__(self):
        PAIALogger().info("PAIAApplication Shutting down")
        for server in self.servers:
            PAIALogger().info(f"Thread[{self.__getCurrentThread().name}] Shutting down {str(server)}")
            server.server_close()
        
        
        
if __name__ == "__main__":
    try:
        app = PAIAApplication()
        app.run()
    except KeyboardInterrupt:
        app.__del__()

