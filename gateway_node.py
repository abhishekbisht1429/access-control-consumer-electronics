import json
import os
import shelve
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse
from handler import sd_request_handler
from gateway_config import config, logging


class ServerRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Split path into its components
        path = parse.urlparse(self.path).path
        path_components = path.split(os.path.sep)
        # print("get: ", path_components)

        # check if appropriate number of parameters have been provided
        if len(path_components) < 2:
            self.send_error(404)
            self.end_headers()
            return

        # headers
        # print(self.headers.keys())
        content_len = self.headers.get('Content-Length')
        if content_len is None:
            self.send_error(411)
            self.end_headers()
            return
        content_len = int(content_len)

        # delegate the task to appropriate handler
        res_body = None
        data = None
        if content_len > 0:
            data = self.rfile.read(content_len)
        if path_components[1] == "gateway_node":
            res_code, res_body = sd_request_handler.handle(path_components[2:],
                                                           data)
        print(res_body)

        # return response to the server
        self.send_response(res_code, self.responses[res_code][0])
        self.end_headers()

        if res_code == 200:
            self.wfile.write(res_body)


if __name__ == '__main__':
    # if len(sys.argv) < 3:
    #     print("Invalid number of args")
    #     exit(1)
    # addr = (sys.argv[1], int(sys.argv[2]))
    addr = (config['server_ip'], config['server_port'])
    server = HTTPServer(addr, ServerRequestHandler)
    logging.info("serving requests from %s", addr)
    server.serve_forever()