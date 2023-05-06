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

def savestim(frames, filename, coherence=None, direction=None):
    gray = []
    for frame in frames:
        gray.append(frame.convert('L'))
    movie = np.stack(gray)
    np.savez_compressed(filename, stim=movie, coherence=coherence, direction=direction)


def main():
    # configuration
    config = {
        'signal':   'same',
        'noise':    'direction',
        'ndots':    300,
        'size':     5,
        'life':     5,
        'speed':    3,
        'duration': [0,2],
        'skipped':  0,
        # 'coherence': [100, 100, 80, 80, 50, 50, 30, 30],
        # 'coherence': [100] * 10,
        'coherence': list(range(100, 0, -10)),
    }

    dur_isi = 1

    # initialization
    cwd = os.path.dirname(os.path.abspath(__file__))
    os.chdir(cwd)

    win = visual.Window(
        size=(400,400),
        fullscr=False,
        screen=0,
        allowGUI=True,
        color=[0,0,0],
        colorSpace='rgb',
        units='pix',
        monitor='testMonitor',
    )
    win.mouseVisible = True
    keybd = keyboard.Keyboard()

    fps = win.getActualFrameRate()
    print(f'Refresh rate = {fps} Hz')
    fps = 60
    ifi = 1/fps

    isi = core.StaticPeriod(win=win)

    # instruction
    text_instr = visual.TextStim(
        win=win,
        name='text_instr',
        text='',
        font='Arial',
        color='white',
        pos=(0, 0),
        height=48,
    )

    # the dot stimulus have to be create after configuration
    dota = visual.DotStim(
        win=win,
        name='dota',
        signalDots=config['signal'],
        noiseDots=config['noise'],
        nDots=config['ndots']//2,
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
    dotb = visual.DotStim(
        win=win,
        name='dotb',
        signalDots=config['signal'],
        noiseDots=config['noise'],
        nDots=config['ndots']//2,
        dotSize=config['size'],
        speed=config['speed'],
        dotLife=config['life'],
        dir=0,
        coherence=0.5,
        fieldPos=(0, 0),
        fieldSize=270,
        # fieldAnchor='center',
        fieldShape='circle',
        color='black',
    )
    clock = core.Clock()

    text_instr.setText('Space or Enter to start')
    text_instr.draw()
    win.flip()

    keybd.waitKeys(keyList=['space', 'enter'])
    win.recordFrameIntervals = True

    for thiscoh in config['coherence']:
        # the trial:
        realdir = ['left', 'right']
        thisdir = np.random.randint(2)
        # thisdir = 0

        dota.dir = 180 * (1 - thisdir)
        dota.coherence = thiscoh / 100
        dotb.dir = 180 * (1 - thisdir)
        dotb.coherence = thiscoh / 100

        win.movieFrames = []
        clock.reset()
        # nframes = int(config['duration']/ifi)
        while clock.getTime() < config['duration'][0]+config['duration'][1]:
        # for ff in range(nframes):
            dota.draw()
            dotb.draw()
            win.flip(True)
            win.getMovieFrame()

            core.wait(ifi*config['skipped'])
            if clock.getTime() > config['duration'][0]:
                a, b = dota.color, dotb.color
                dota.setColor(b)
                dotb.setColor(a)
            pass

        # save an extra blank screen for separation in frame streams
        win.flip(True)

        isi.start(dur_isi)
        savestim(win.movieFrames, f'revphi-{thiscoh}{realdir[thisdir][0]}.npz', thiscoh, realdir[thisdir])
        isi.complete()
        # check post events directly for remote response:

if __name__ == '__main__':
    main()

