# server.py
import argparse
import http.server
import socket
import threading
import time

from paia import *


class PAIAApplication:
    def __init__(self):
        PAIALogger().info("PAIAApplication Start")
        self.servers = {}
        self.ui_server_thread = None
        self.service_server_thread = None
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
            
    def run_server(self,id:str, host :str = "localhost", port :int = 8000, server : type = http.server.ThreadingHTTPServer, handler: type = http.server.BaseHTTPRequestHandler, description : str = "Default server" ,retry_count :int = 3,retry_wait : int = 10):
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
                        self.servers[id] = srv
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
            id="ui",
            host=PAIAConfig().ui_host,
            port=PAIAConfig().ui_port,
            server=PAIAUIServer,
            handler=PAIAUIHandler,
            description="UI Server"
        )
 
    
    def service_server(self):
        self.run_server(
            id="service",
            host="0.0.0.0",
            port=PAIAConfig().port,
            server=PAIAServiceServer,
            handler=PAIAServiceHandler,
            description="Service Server"
        )

    def run(self):
        if PAIAConfig().getConfig().get("ui",{}).get("autostart",True):
            self.ui_server_thread = threading.Thread(target=self.ui_server, name="UI Thread",)
            self.ui_server_thread.start()
        self.service_server_thread = threading.Thread(target=self.service_server, daemon=True,name="Service Thread")
        self.service_server_thread.start()
        while True:
            time.sleep(1)
    
    def __del__(self):
        PAIALogger().info("PAIAApplication Shutting down")
        for server in self.servers:
            PAIALogger().info(f"Thread[{self.__getCurrentThread().name}] Shutting down server {id} {str(server)}")
            self.servers[server].server_close()
        
        
if __name__ == "__main__":
    try:
        app = PAIAApplication()
        app.run()
    except KeyboardInterrupt:
        app.__del__()

