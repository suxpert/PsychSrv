#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import division

import os
import numpy as np
import random

from psychopy import core
from psychopy import visual
from psychopy import data

from psychopy.hardware import keyboard
from PsychoServer import PsychoServer


def savestim(frames, filename, coherence=None, direction=None):
    gray = []
    for frame in frames:
        gray.append(frame.convert('L'))
    movie = np.stack(gray)
    np.savez_compressed(filename, stim=movie, coherence=coherence, direction=direction)


def randcoh(level, ntrials, factor=None):
    adapt = [
        [-1,  1] * 2,
        [-1,  1] * 3,
        [-1,  1] * 4,
        [-1,  1] * 5,
        # [-1,  1] * 6,
        [-1,  0,  1] * 2,
        [-1,  0,  1] * 3,
        [-1,  0,  1] * 4,
        [-1,  0,  1] * 5,
        [-1,  0,  1] * 6,
        [-3, -1,  1,  3] * 2,
        [-3, -1,  1,  3] * 3,
        [-3, -1,  1,  3] * 4,
        [-3, -1,  1,  3] * 5,
        [-2, -1,  0,  1,  2] * 2,
        [-2, -1,  0,  1,  2] * 3,
        [-2, -1,  0,  1,  2] * 4,
        [-5, -3, -1,  1,  3,  5] * 2,
        [-5, -3, -1,  1,  3,  5] * 3,
        [-3, -2, -1,  0,  1,  2,  3] * 2,
        # [-7, -5, -3, -1,  1,  3,  5,  7],
        # [-5, -3, -2, -1,  0,  1,  2,  3, 5],
    ]
    scale = [
        [],
        [5,15],
        [3,8],
        [2,5],
        [1,4],
        [1,3],
    ]
    cands = [l for l in adapt if len(l) == ntrials]
    if len(cands) == 0:
        cands = [l for l in adapt if len(l) == ntrials+1]
    if len(cands) == 0:
        cands = [l for l in adapt if len(l) == ntrials+2]

    choose = random.choice(cands)

    if factor is None:
        tmp = scale[max(choose)]
        factor = np.random.randint(tmp[0],tmp[1])
    coherence = level + np.array(choose) * factor
    return coherence


def main():
    # configuration
    countdown = 3
    dur_isi = 1
    blk_iti = 2

    # initialization
    cwd = os.path.dirname(os.path.abspath(__file__))
    os.chdir(cwd)

    if not os.path.isdir('run'):
        os.mkdir('run')

    ps = PsychoServer(size=(300,300), port=8080, verbose=True)
    ps.move(0, -50)
    isi = core.StaticPeriod(win=ps.win)
    keybd = keyboard.Keyboard(backend='iohub')

    result = {
        'trial': [],
        'coherence': [],
        'direction': [],
        'response': [],
        'rt': [],
        'correct': [],
    }

    print(f'Refresh rate = {ps.fps} Hz')
    # always assume a 60Hz screen, the above fps always change
    dur = 1/60

    ps.start()
    # ps.set_state(state="listening")
    # ps.show_info(f'Listening at {ps.server_addr}')

    # waiting for connection with an ugly loop
    # ps.wait_query('get', '/')

    block = 0
    while ps.running:
        ps.set_state(state="waiting")
        ps.show_info(f'Waiting at\n{ps.server_addr}')

        # waiting for configuration with an ugly loop
        ps.clear_cache(clear_posts=True)
        while ps.running:
            config = ps.wait_query('post', '/')
            if 'ntrials' in config:
                break
        ps.set_state(state="prepare")
        block += 1

        # config = {
        #     'signal': 'same',
        #     'noise': 'direction',
        #     'ndots': 300,
        #     'size': 5,
        #     'life': 3,
        #     'speed': 3,
        #     'ntrials': 8,
        #     'duration': 2,
        # }

        ntrials = config['ntrials']

        # the dot stimulus have to be create after configuration
        dots = visual.DotStim(
            win=ps.win,
            name='dots',
            signalDots=config['signal'],
            noiseDots=config['noise'],
            nDots=config['ndots'],
            dotSize=config['size'],
            speed=config['speed'],
            dotLife=config['life'],
            dir=0,
            coherence=0.5,
            fieldPos=(0, 0),
            fieldSize=270,
            # fieldAnchor='center',
            fieldShape='circle',
            color='white',
        )

        # counting down
        for ff in range(int(countdown/dur)):
            ps.show_info(f'{ntrials} trials for block {block}\nin {countdown-int(ff*dur)}')
            ps.flip()
        ps.show_info()

        # prepare trial order and loop for trials
        coherence = randcoh(config['coherence'], ntrials)
        for trial in range(ntrials):
            # the trial:
            realdir = ['left', 'right']
            thisdir = np.random.randint(2)
            thiscoh = coherence[trial]

            dots.dir = 180 * (1 - thisdir)
            dots.coherence = thiscoh / 100

            ps.clear_cache()
            ps.win.callOnFlip(keybd.clock.reset)
            ps.win.callOnFlip(keybd.clearEvents)
            # ps.win.callOnFlip(timer.reset)
            ps.win.callOnFlip(ps.set_state,
                state="stim",
                block=block,
                trial=trial,
                remain=ntrials-trial-1,
                direction=realdir[thisdir],
                coherence=int(thiscoh),
            )

            nframes = int(config['duration']/dur)
            for ff in range(nframes):
                dots.draw()
                ps.show_fixation()
                ps.flip(True)

            # save an extra blank screen for separation in frame streams
            ps.show_fixation()
            ps.flip(True)

            isi.start(dur_isi)
            savestim(ps.win.movieFrames, f'run/block-{block}_trial-{trial}.npz', thiscoh, realdir[thisdir])
            # set status after stimulus saved, so that client can wait for isi as an event
            ps.set_state(
                state="isi",
                block=block,
                trial=trial,
                remain=ntrials-trial-1,
            )
            # or wait until all frames have been fetched
            # ps.sync_frame()

            isi.complete()
            # check for simulated key press
            resp = keybd.getKeys(keyList=['left', 'right'])

            if len(resp) == 0:
                ch = ''
                rt = np.nan
                fb = 'miss'
                print(f'trial {trial}: miss!', realdir[thisdir])
            else:
                ch = resp[-1].name
                rt = resp[-1].rt
                if ch == realdir[thisdir]:
                    fb = 'correct'
                else:
                    fb = 'error'
                print(f'trial {trial}: {fb}', realdir[thisdir], ch, rt)

            result['trial'].append(trial)
            result['coherence'].append(thiscoh)
            result['direction'].append(realdir[thisdir])
            result['response'].append(ch)
            result['rt'].append(rt)
            result['correct'].append(fb)

        # after all trials done: report some results
        np.savez(f'run/rdmtask-{block}-{data.getDateStr()}.npz', **result)
        ps.set_state(state="finished")
        ps.sleep(blk_iti)


if __name__ == '__main__':
    main()

