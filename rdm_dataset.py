#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import division

import os
import sys
import numpy as np

from psychopy import core
from psychopy import visual
from psychopy.hardware import keyboard


def savestim(frames, filename, coherence=None, direction=None):
    gray = []
    for frame in frames:
        gray.append(frame.convert('L'))
    movie = np.stack(gray)
    np.savez_compressed(filename, stim=movie, coherence=coherence, direction=direction)


def main():
    # some initialization

    cwd = os.path.dirname(os.path.abspath(__file__))
    os.chdir(cwd)

    win = visual.Window(
        size=(300,300),
        fullscr=False,
        screen=0,
        allowGUI=True,
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
    
    # for c in range(100):
    for c in [60, 50, 40, 30, 20, 10]:
        for r in range(10):
            for a in [0, 180]:
                if a == 0:
                    d = 'right'
                else:
                    d = 'left'
                text_instr.setText(f'c{c}{d[0]}-{r}')
                text_instr.draw()
                win.flip()
                core.wait(0.5)

                dots = visual.DotStim(
                    win=win,
                    signalDots='same',
                    noiseDots='direction',
                    nDots=200,
                    dotSize=6,
                    dotLife=4,
                    speed=2,
                    dir=a,
                    coherence=c/100,
                    fieldPos=(0, 0),
                    fieldSize=270,
                    fieldAnchor='center',
                    fieldShape='circle',
                    color='white',
                )

                # skip the very first frame?
                # dots.draw()
                # win.flip()

                for ff in range(fps*2):
                    dots.draw()
                    win.flip()
                    win.getMovieFrame()
                    if keybd.getKeys(keyList=["escape"]):
                        core.quit()

                win.flip()
                savestim(win.movieFrames, f'data/c{c}{d[0]}-{r}.npz', c, d)
                win.movieFrames = []


if __name__ == '__main__':
    main()

