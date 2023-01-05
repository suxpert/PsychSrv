#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import division

import os
import sys
import numpy as np

from psychopy import core
from psychopy import visual
from psychopy.hardware import keyboard

def savedots(win, dots, filename):
    dur = 1
    fps = 60
    nfs = dur * fps
    for ff in range(nfs):
        dots.draw()
        win.flip()
        win.getMovieFrame()

    win.flip()
    win.saveMovieFrames(filename, fps=30)


def main():
    # some initialization

    cwd = os.path.dirname(os.path.abspath(__file__))
    os.chdir(cwd)

    win = visual.Window(
        size=(400,400),
        fullscr=False,
        screen=0,
        allowGUI=False,
        color=[-1,-1,-1],
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
        color='white',
        pos=(0, 0),
        height=48,
    )

    text_instr.setText('Space or Enter\nto start')
    text_instr.draw()
    win.flip()

    keybd.waitKeys(keyList=['space', 'enter'])

    opt_signal = ['same', 'different']
    opt_noise  = ['position', 'direction', 'walk']
    opt_dir    = [0, 90, 180, 270]
    for s in opt_signal:
        for n in opt_noise:
            for d in opt_dir:
                text_instr.setText(f'{s}-{n}-{d}')
                text_instr.draw()
                win.flip()
                core.wait(1)

                dots = visual.DotStim(
                    win=win,
                    signalDots=s,
                    noiseDots=n,
                    nDots=200,
                    dotSize=5,
                    dotLife=8,
                    speed=2,
                    dir=d,
                    coherence=0.8,
                    fieldPos=(0, 0),
                    fieldSize=300,
                    fieldAnchor='center',
                    fieldShape='circle',
                    color='white',
                )

                savedots(win, dots, f'demo_{s}-{n}-{d}.gif')


if __name__ == '__main__':
    main()

