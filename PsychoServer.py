#!/usr/bin/env python3


import socket
import json
import pyautogui
import threading

from http.server import SimpleHTTPRequestHandler, HTTPServer
from psychopy import core


class MyHTTPServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.server_addr = '%s:%d' % (socket.gethostbyname(self.server_name), self.server_port)
        self.server_thread = threading.Thread(target=self.serve_forever)
        self.mesg = 'init'
        self.stat = {}
    
    def set_state(self, mesg='', stat={}):
        self.mesg = mesg
        self.stat = stat
    
    def get_state(self, clear=True):
        mesg = self.mesg
        stat = self.stat
        if clear:
            self.set_state()
        return mesg, stat

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
        self.send_header('Accept', 'application/json')
        # self.send_header('Content-type', 'application/json')
        self.send_header('Content-type', self.extensions_map[type])
        self.end_headers()

    def do_GET(self):
        if self.path == '/status':
            # send status as json to client
            mesg, state = self.server.get_state(False)
            self._set_headers('.json')
            self.wfile.write(json.dumps(state).encode("utf-8"))
            # if mesg == 'sync':
            #     self._set_headers('.json')
            #     self.wfile.write(json.dumps(state))
            # else:
            #     pass
        else:
            SimpleHTTPRequestHandler.do_GET(self)
        state = {
            "client": self.headers['User-Agent']
        }
        self.server.set_state('get: '+ self.path, state)

    def do_POST(self):
        res = {}
        length = int(self.headers['Content-Length'])
        content = self.rfile.read(length)
        print(self.headers)
        print(content)
        if self.headers['Content-Type'] == 'application/json':
            res = json.loads(content)
            print(res)
            if 'response' in res:
                # simulate key press
                pyautogui.press(res['response'])

        mesg, state = self.server.get_state(False)
        self._set_headers('.json')
        self.wfile.write(json.dumps(state).encode("utf-8"))

        res['client'] = self.headers['User-Agent']
        self.server.set_state('post: ' + self.path, res)


def setupserver(addr='0.0.0.0', port=8080):
    return MyHTTPServer((addr, port), MyRequestHandler)


def main():
    httpd = setupserver()
    httpd.run()
#    httpd.start()
#    for ii in range(20):
#        mesg, stat = httpd.get_state()
#        print(stat)
#        core.wait(0.5)
#
#    httpd.stop()



if __name__ == '__main__':
    main()
