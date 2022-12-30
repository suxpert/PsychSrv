#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import division

import os
import sys
import numpy as np
import random

from psychopy import core
from psychopy import event
from psychopy import visual
from psychopy import data
# logging, clock

from psychopy.hardware import keyboard

from PsychoServer import setupserver


def savestim(frames, filename, coherence=None, direction=None):
    gray = []
    for frame in frames:
        gray.append(frame.convert('L'))
    movie = np.stack(gray)
    np.savez_compressed(filename, stim=movie, coherence=coherence, direction=direction)


def cleanup(win=None, httpd=None):
    if httpd is not None:
        httpd.stop()
    if win is not None:
        win.close()

    core.quit()


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
    # some initialization

    cwd = os.path.dirname(os.path.abspath(__file__))
    os.chdir(cwd)

    if not os.path.isdir('run'):
        os.mkdir('run')

    win = visual.Window(
        size=(500,500),
        fullscr=False,
        screen=0,
        # allowGUI=False,
        color='black',
        colorSpace='rgb',
        units='pix',
        monitor='testMonitor',
    )
    win.mouseVisible = True
    # on my computer, only iohub is fully compatible with pyautoui
    keybd = keyboard.Keyboard()

    expinfo = {
        'date': data.getDateStr(),
        'name': os.path.basename(__file__)[:-3],
        'cwd': cwd,
        'fps': win.getActualFrameRate(),
    }
    result = {
        'trial': [],
        'coherence': [],
        'direction': [],
        'response': [],
        'rt': [],
        'correct': [],
    }

    print(f'Refresh rate = {expinfo["fps"]} Hz')
    # always assume a 60Hz screen, the above fps always change
    expinfo['fps'] = 60
    dur = 1/60

    # prepare components
    # static ISI and fixation
    isi = core.StaticPeriod(win=win)
    fixation = visual.ShapeStim(
        win=win,
        name='fixation',
        vertices='cross',
        size=(10, 10),
        ori=0,
        pos=(0, 0),
        # anchor='center',
        lineWidth=0,
        lineColor=None,
        fillColor='red',
    )

    # instruction
    text_instr = visual.TextStim(
        win=win,
        name='instr',
        text='Preparing...',
        font='Arial',
        color='white',
        pos=(0, 0),
        height=36,
    )

    # we can reuse instruction as countdown
    text_countdown = visual.TextStim(
        win=win,
        name='countdown',
        text='',
        font='Arial',
        color='white',
        pos=(0, 0),
        height=48,
    )

    text_instr.setAutoDraw(True)
    win.flip()

    # setup server and wait for connection
    httpd = setupserver()
    httpd.start()

    event.globalKeys.clear()
    event.globalKeys.add(key='escape', func=cleanup, func_kwargs={'win': win, 'httpd': httpd})

    httpd.set_state(
        state="listening",
    )
    text_instr.setText(f'Listening at {httpd.server_addr}')

    # ugly waiting for connection
    while True:
        win.flip()
        core.wait(0.1)
        query, param = httpd.get_query(True)
        if query == 'get: /':
            # some one is requesting the home page
            break;
        if keybd.getKeys(keyList=['escape']):
            cleanup(win=win, httpd=httpd)

    while True:
        httpd.set_state(state="waiting")
        text_instr.setText('Waiting configuration')
        text_instr.setAutoDraw(True)
        win.flip()

        # configuration from remote
        while True:
            win.flip()
            core.wait(0.1)
            query, param = httpd.get_query(True)
            if query == 'post: /':
                break;
            if keybd.getKeys(keyList=['escape']):
                cleanup(win=win, httpd=httpd)

        httpd.set_state(state="config")

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
        config = param

        ntrials = config['ntrials']
        text_instr.setText(f'Will run {ntrials} trials')
        # text_instr.draw()
        win.flip()

        core.wait(0.5)
        text_instr.setAutoDraw(False)

        httpd.set_state(state="prepare")

        # the dot stimulus have to be create after configuration
        dots = visual.DotStim(
            win=win,
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
        timer = core.Clock()
        countdown = 3
        httpd.set_state(state="countdown")
        for ff in range(int(countdown/dur)):
        # while timer.getTime() < 5:
            # text_countdown.setText=(str(5-int(timer.getTime())))
            text_countdown.setText(str(countdown-int(ff*dur)))
            text_countdown.draw()
            win.flip()

        # prepare trial order and loop for trials
        coherence = randcoh(config['coherence'], ntrials)
        for trial in range(ntrials):
            # the trial:
            realdir = ['left', 'right']
            thisdir = np.random.randint(2)
            thiscoh = coherence[trial]

            dots.dir = 180 * (1 - thisdir)
            dots.coherence = thiscoh / 100

            win.callOnFlip(keybd.clock.reset)
            win.callOnFlip(keybd.clearEvents)
            win.callOnFlip(timer.reset)
            win.callOnFlip(httpd.set_state,
                state="stim",
                trial=trial,
                remain=ntrials-trial-1,
                direction=realdir[thisdir],
                coherence=int(thiscoh),
            )

            nframes = int(config['duration']/dur)
            for ff in range(nframes):
                dots.draw()
                fixation.draw()
                win.flip()
                win.getMovieFrame()

            fixation.draw()
            t = win.flip()

            isi.start(0.5)
            httpd.set_state(
                state="isi",
                trial=trial,
                remain=ntrials-trial-1,
            )

            savestim(win.movieFrames, f'run/trial-{trial}.npz', thiscoh, realdir[thisdir])
            # win.saveMovieFrames(f'dots-{trial}.gif', fps=expinfo['fps'])
            win.movieFrames = []

            isi.complete()
            resp = keybd.getKeys(keyList=['left', 'right'])
            # resp = keybd.waitKeys(0.5, keyList=['left', 'right'], clear=False)

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

            # keybd.clearEvents()
            result['trial'].append(trial)
            result['coherence'].append(thiscoh)
            result['direction'].append(realdir[thisdir])
            result['response'].append(ch)
            result['rt'].append(rt)
            result['correct'].append(fb)

        # after all trials done: report some results
        np.savez(f'run/{expinfo["name"]}-{expinfo["date"]}.npz', **result)
        httpd.set_state(state="finished")
        core.wait(2)

    cleanup(win=win, httpd=httpd)


if __name__ == '__main__':
    main()

