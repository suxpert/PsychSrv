#!/usr/bin/env python3


from __future__ import division

import requests
import time


class client():
    def __init__(self, ip, port, verbose=True):
        self.address = f'http://{ip}:{port}'
        self.verbose = verbose

    def get_state(self, timeout=0.2):
        url = self.address + '/status'
        try:
            req = requests.get(url, timeout=timeout)
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
                req = requests.get(url, timeout=timeout)
                if self.verbose:
                    print(req.content)
                if req.ok and req.headers['Content-Type'] == 'application/json':
                    ret = req.json()
                    if 'state' in ret and ret['state'] == state:
                        return ret
            # except requests.ConnectionError as e:
            except Exception as e:
                if self.verbose:
                    print(e)
            time.sleep(interval)


def main():
    pass


if __name__ == '__main__':
    main()
