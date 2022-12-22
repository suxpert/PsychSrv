#!/usr/bin/env python3


import socket
import json
import pyautogui
import threading

from http.server import SimpleHTTPRequestHandler, HTTPServer
# from psychopy import core


class MyHTTPServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.server_addr = '%s:%d' % (socket.gethostbyname(self.server_name), self.server_port)
        self.server_thread = threading.Thread(target=self.serve_forever)
        self.state = {'state': 'init'}
        self.query = ('', {})
    
    def set_state(self, **kwargs):
        if kwargs:
            print('state = ', kwargs)
        self.state = kwargs
    
    def set_query(self, query='', **kwargs):
        if kwargs:
            print(f"query = '{query}', ", kwargs)
        self.query = (query, kwargs)

    def get_query(self, clear=False):
        query, param = self.query
        if clear:
            self.query = ('', {})
        return query, param

    def run(self):
            try:
                self.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                # Clean-up server (close socket, etc.)
                self.server_close()

    def start(self):
        self.server_thread.start()

    def stop(self):
        self.shutdown()
        self.server_thread.join()


class MyRequestHandler(SimpleHTTPRequestHandler):
    def _set_headers(self, type='.html'):
        self.send_response(200)
        # self.send_header('Accept', 'application/json')
        # self.send_header('Content-type', 'application/json')
        self.send_header('Content-type', self.extensions_map[type])
        self.end_headers()

    def do_GET(self):
        if self.path == '/status':
            # send status as json to client
            state = json.dumps(self.server.state)
            self._set_headers('.json')
            self.wfile.write(state.encode("utf-8"))
        else:
            SimpleHTTPRequestHandler.do_GET(self)

        self.server.set_query(f'get: {self.path}',
            client=self.headers['User-Agent'],
        )

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        content = self.rfile.read(length)

        if self.headers['Content-Type'] == 'application/json':
            param = json.loads(content)
            # print(param)
            if 'response' in param:
                # simulate key press
                pyautogui.press(param['response'])
        else:
            param = {'content': content}
            # print(content)

        state = json.dumps(self.server.state)
        self._set_headers('.json')
        self.wfile.write(state.encode("utf-8"))

        param['client'] = self.headers['User-Agent']
        self.server.set_query(f'post: {self.path}', **param)


def setupserver(addr='0.0.0.0', port=8080):
    return MyHTTPServer((addr, port), MyRequestHandler)


def main():
    httpd = setupserver()
    httpd.run()

#    httpd.start()
#    for ii in range(20):
#        query, param = httpd.get_query()
#        core.wait(0.5)
#
#    httpd.stop()


if __name__ == '__main__':
    main()

