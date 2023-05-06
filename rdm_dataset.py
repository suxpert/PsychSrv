#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import division

import os
import sys
import numpy as np
import yaml

from psychopy import core
from psychopy import visual
from psychopy.hardware import keyboard


def savestim(frames, filename, coherence=None, direction=None, speed=None):
    gray = []
    for frame in frames:
        gray.append(frame.convert('L'))
    movie = np.stack(gray)
    np.savez_compressed(filename, stim=movie, coherence=coherence, direction=direction, speed=speed)


def main():
    # configuration:
    config = {
        'folder': 'dataset-2',
        'signaldots': 'same',
        # 'signaldots': 'different',
        # 'noisedots': 'position',
        'noisedots': 'walk',
        # 'noisedots': 'direction',
        'direction': ['left', 'right'],
        # 'direction': ['up', 'down'],
        # 'coherence': list(range(99,0,-1)),
        'coherence': list(range(40,0,-1)),
        'repeat': 10,
        'ndots': 200,
        'dotsize': list(range(1, 10)),
        'dotlife': 4,
        'speed': list(range(1, 10)),
        'dim': [300, 300],
        'nframes': 120,
        'bgcolor': 'black',
        # 'bgcolor': 'white',
        'color': 'white',
        # 'color': 'black',
    }

    # some initialization
    cwd = os.path.dirname(os.path.abspath(__file__))
    os.chdir(cwd)


    folder = config['folder']
    if not os.path.isdir(folder):
        os.mkdir(folder)

    cfgfile = os.path.join(folder, '_meta.txt')
    if os.path.exists(cfgfile):
        raise FileExistsError('Config file exist! dataset is not empty!')

    with open(cfgfile, 'w') as file:
        yaml.dump(config, file)

    win = visual.Window(
        size=config['dim'],
        fullscr=False,
        screen=0,
        allowGUI=True,
        color=config['bgcolor'],
        colorSpace='rgb',
        units='pix',
        monitor='testMonitor',
    )
    win.mouseVisible = True
    keybd = keyboard.Keyboard()

    fps = win.getActualFrameRate()
    print(f'Refresh rate = {fps} Hz')
    fps = 60

    # instruction
    text_instr = visual.TextStim(
        win=win,
        name='text_instr',
        text='',
        font='Arial',
        color=config['color'],
        pos=(0, 0),
        height=24,
    )

    text_instr.setText('Space or Enter to start')
    text_instr.draw()
    win.flip()

    keybd.waitKeys(keyList=['space', 'return'])

    sz = ' abcdefghijklmnopqrst'
    # for c in [60, 50, 40, 30, 20, 10]:
    for c in config['coherence']:
        for d in config['direction']:
            if d == 'left':
                a = 180
            elif d == 'right':
                a = 0
            elif d == 'up':
                a = 90
            elif d == 'down':
                a = 270

            for v in config['speed']:
                for s in config['dotsize']:
                    for r in range(config['repeat']):

                        fname = f'{sz[s]}{c:02d}{d[0]}{v}-{r:02d}'
                        text_instr.setText(fname)
                        text_instr.draw()
                        win.flip()
                        core.wait(0.1)

                        dots = visual.DotStim(
                            win=win,
                            signalDots=config['signaldots'],
                            noiseDots=config['noisedots'],
                            nDots=config['ndots'],
                            dotSize=s,
                            dotLife=config['dotlife'],
                            speed=v,
                            dir=a,
                            coherence=c/100,
                            fieldPos=(0, 0),
                            fieldSize=270,
                            fieldAnchor='center',
                            fieldShape='circle',
                            color=config['color'],
                        )

                        # skip the very first frame?
                        # dots.draw()
                        # win.flip()

                        for ff in range(config['nframes']):
                            dots.draw()
                            win.flip()
                            win.getMovieFrame()
                            # if keybd.getKeys(keyList=["escape"]):
                            if keybd.getKeys(keyList=["pause"]):
                                core.quit()

                        win.flip()
                        savestim(win.movieFrames, f'{folder}/{fname}.npz', c, d, v)
                        win.movieFrames = []


if __name__ == '__main__':
    main()

