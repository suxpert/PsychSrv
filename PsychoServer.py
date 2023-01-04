#!/usr/bin/env python3


from __future__ import division

import socket
import json
import pyautogui
import threading
# import time
import io

from http.server import SimpleHTTPRequestHandler, HTTPServer

from psychopy import core
from psychopy import event
from psychopy import visual

from pyglet.libs.win32 import _user32, constants
# from psychopy.hardware import keyboard


class PsychoRequestHandler(SimpleHTTPRequestHandler):
    def _set_headers(self, type='.html'):
        self.send_response(200)
        self.send_header('Content-type', self.extensions_map[type])
        self.end_headers()

    def do_GET(self):
        if self.path == '/status':
            # send status as json to client
            state = json.dumps(self.server.state)
            self._set_headers('.json')
            self.wfile.write(state.encode("utf-8"))
        elif self.path == '/get_delay':
            nframes = len(self.server.win.movieFrames)
            self._set_headers('.html')
            self.wfile.write(f'{nframes}'.encode("utf-8"))
        elif self.path == '/get_frame' or self.path == '/get_gray':
            # return a png image
            frame = self.server.get_frame()
            if self == '/get_gray':
                frame = frame.convert('L')
            if frame is not None:
                with io.BytesIO() as buff:
                    frame.save(buff, format='png')
                    self._set_headers('.png')
                    self.wfile.write(buff.getvalue())
            else:
                self._set_headers('.html')

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


class PsychoServer(HTTPServer):
    def __init__(self, size, fullscr=False, port=8080, verbose=True):
        super().__init__(('0.0.0.0', port), PsychoRequestHandler)
        self.server_addr = '%s:%d' % (socket.gethostbyname(self.server_name), self.server_port)
        self.server_thread = threading.Thread(target=self.serve_forever)
        self.state = {'state': 'init'}
        self.query = ('', {})
        self.verbose = verbose
        self.running = True

        self.win = visual.Window(
            size=size,
            fullscr=fullscr,
            screen=0,
            allowGUI=False,
            color='black',
            colorSpace='rgb',
            units='pix',
            monitor='testMonitor',
            winType='pyglet',
        )
        self.win.mouseVisible = True

        # make the window top-most
        _user32.SetWindowPos(
            self.win.winHandle._hwnd,
            constants.HWND_TOPMOST, 0, 0, 0, 0,
            constants.SWP_NOMOVE | constants.SWP_NOSIZE | constants.SWP_SHOWWINDOW
        )

        self.fps = self.win.getActualFrameRate()
        self.timer = core.Clock()

        self._info = visual.TextStim(
            win=self.win,
            text='Initializing',
            font='Arial',
            color='white',
            pos=(0, 0),
            height=36,
        )

        self._fixation = visual.ShapeStim(
            win=self.win,
            vertices='cross',
            size=(10, 10),
            ori=0,
            pos=(0, 0),
            # anchor='center',
            lineWidth=0,
            lineColor=None,
            fillColor='red',
        )

        event.globalKeys.clear()
        event.globalKeys.add(key='escape', func=self.__del__)
        event.globalKeys.add(key='q', modifiers=['ctrl'], func=self.__del__)

        self.show_info('Initializing')
        self.flip()

    def start(self):
        '''
        async serve forever in background
        '''
        self.running = True
        self.server_thread.start()

    def stop(self):
        '''
        stop the serve forever thread
        '''
        self.running = False
        self.shutdown()
        self.server_thread.join()

    def __del__(self):
        self.stop()
        self.win.close()
        # exit might cause a wait forever on windows:
        # exception ignored on calling ctypes callback function
        # core.quit()

    def run(self):
        self.start()
        while self.running:
            q, _ = self.get_query(True)
            if q:
                self.show_info(q)
                self.flip(True)
            self.sleep(0.1)

    def sleep(self, interval):
        core.wait(interval, hogCPUperiod=0.05)

    def set_state(self, **kwargs):
        '''
        set server state, which can be fetched using http get
        '''
        if self.verbose and kwargs:
            print('state = ', kwargs)
        self.state = kwargs

    def get_state(self):
        return self.state

    def wait_state(self, state, interval=0.1):
        while True:
            if self.state['state'] == state:
                return self.server.state
            self.sleep(interval)

    def set_query(self, query='', **kwargs):
        '''
        set request infomation, to be used in request callback
        '''
        if self.verbose and kwargs:
            print(f"query = '{query}', ", kwargs)
        self.query = (query, kwargs)

    def get_query(self, clear=False):
        '''
        get the last request info
        '''
        query, param = self.query
        if clear:
            self.query = ('', {})
        return query, param

    def wait_query(self, query, interval=0.1):
        while True:
            q, param = self.get_query(True)
            if q == query:
                return param
            self.sleep(interval)

    def flip(self, cache=False):
        self.win.flip()
        if cache:
            self.win.getMovieFrame()

    def get_frame(self):
        if len(self.win.movieFrames) > 0:
            return self.win.movieFrames.pop(0)
        else:
            return None

    def clear_cache(self):
        self.win.movieFrames = []

    def show_info(self, info):
        if info:
            self._info.setText(info)
            self._info.setAutoDraw(True)
        else:
            self._info.setAutoDraw(False)

    def show_fixation(self):
        self._fixation.draw()


def main():
    ps = PsychoServer(size=(500,500), port=8080)
    ps.run()


if __name__ == '__main__':
    main()
