#!/usr/bin/env python3


from __future__ import division

import requests
import time
import numpy as np

from PIL import Image


class PsychoClient():
    def __init__(self, ip, port, verbose=True):
        self.address = f'http://{ip}:{port}'
        self.session = requests.Session()
        self.verbose = verbose
        self.session.verify = True

    def send_command(self, command='noop', timeout=0.2):
        url = self.address + '/'
        data = {'control': command}
        try:
            req = self.session.post(url, json=data, timeout=timeout)
            if req.ok and req.headers['Content-Type'] == 'application/json':
                state = req.json()
            else:
                state = {
                    'code': req.status_code,
                    'content': req.content,
                }
        except Exception as e:
            state = str(e)

        return state

    def get_state(self, timeout=0.2):
        url = self.address + '/status'
        try:
            req = self.session.get(url, timeout=timeout)
            if req.ok and req.headers['Content-Type'] == 'application/json':
                state = req.json()
            else:
                state = {
                    'code': req.status_code,
                    'content': req.content,
                }
        except Exception as e:
            state = str(e)

        return state

    def wait_state(self, state, interval=0.2, timeout=0.2):
        url = self.address + '/status'
        while True:
            try:
                req = self.session.get(url, timeout=timeout)
                if self.verbose:
                    print(req.content)
                if req.ok and req.headers['Content-Type'] == 'application/json':
                    ret = req.json()
                    if 'state' in ret:
                        if isinstance(state, str) and ret['state'] == state:
                            return ret
                        if isinstance(state, list) and ret['state'] in state:
                            return ret
            # except requests.ConnectionError as e:
            except Exception as e:
                if self.verbose:
                    print(e)
            time.sleep(interval)

    def get_frame(self, timeout=0.2):
        # url = self.address + '/frame'
        url = self.address + '/image'
        try:
            req = self.session.get(url, stream=True, timeout=timeout)
            print(req.headers)
            if req.ok and req.headers['Content-Type'] == 'image/png':
                req.raw.decode_content = True
                img = Image.open(req.raw, formats=['png'])
                frame = np.array(img)
            else:
                if self.verbose:
                    print(req.content)
                frame = None
        except Exception as e:
            if self.verbose:
                print(e)
            frame = None

        return frame

    def loop_frame(self, callback: callable, interval=0.1, timeout=0.2):
        # url = self.address + '/frame'
        url = self.address + '/image'
        while True:
            try:
                req = self.session.get(url, stream=True, timeout=timeout)
                if req.ok and req.headers['Content-Type'] == 'image/png':
                    req.raw.decode_content = True
                    img = Image.open(req.raw, formats=['png'])
                    frame = np.array(img)
                    callback(frame)
                else:
                    if self.verbose:
                        print(req.content)
                    time.sleep(interval)
            except Exception as e:
                if self.verbose:
                    print(e)
                time.sleep(interval)


def main():
    import logging
    logging.basicConfig(level=logging.DEBUG)

    client = PsychoClient('127.0.0.1', 8080)
    client.wait_state(['init', 'waiting'])
    while True:
        state = client.get_state()
        print(state)
        if isinstance(state, str):
            # should be some exception, e.g. server is down, so
            break
        time.sleep(2)


if __name__ == '__main__':
    main()
