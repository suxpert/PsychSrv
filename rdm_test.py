#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import division

import os
import sys
import numpy as np

from psychopy import core
from psychopy import visual
from psychopy import data #, event, logging, clock

from psychopy.hardware import keyboard

from PsychoServer import setupserver


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
    keybd = keyboard.Keyboard(backend='iohub')

    expinfo = {
        'date': data.getDateStr(),
        'name': os.path.basename(__file__),
        'cwd': cwd,
        'fps': win.getActualFrameRate(),
    }

    print(f'Refresh rate = {expinfo["fps"]} Hz')
    if expinfo['fps'] is None:
        # fall back to 60Hz
        expinfo['fps'] = 60
        dur = 1/60
    else:
        dur = 1 / round(expinfo['fps'])

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
        anchor='center',
        lineWidth=0,
        lineColor=None,
        fillColor='red',
    )

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

    # we can reuse instruction as countdown
    text_countdown = visual.TextStim(
        win=win,
        name='text_countdown',
        text='',
        font='Arial',
        color='white',
        pos=(0, 0),
        height=48,
    )

    text_instr.setText('Preparing...')
    text_instr.draw()
    win.flip()

    # setup server and wait for connection
    httpd = setupserver()

    text_instr.setText(f'Waiting at\n{httpd.server_addr}')
    text_instr.draw()
    win.flip()

    httpd.handle_request()
    # keybd.waitKeys(keyList=['space', 'enter'])
    text_instr.setText(f'Waiting for configuration')
    text_instr.draw()
    win.flip()
    keybd.waitKeys(keyList=['space', 'enter'])
    httpd.start()
    
    # configuration from remote
    config = {
        'signal': 'same',
        'noise': 'direction',
        'ndots': 300,
        'size': 5,
        'life': 3,
        'speed': 3,
        'ntrials': 8,
        'duration': 2,
    }

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
        fieldSize=300,
        fieldAnchor='center',
        fieldShape='circle',
        color='white',
    )

    # counting down
    timer = core.Clock()
    countdown = 3
    for ff in range(int(countdown/dur)):
    # while timer.getTime() < 5:
        # text_countdown.setText=(str(5-int(timer.getTime())))
        text_countdown.setText(str(countdown-int(ff*dur)))
        text_countdown.draw()
        win.flip()

    # prepare trial order and loop for trials
    for trial in range(config['ntrials']):
        # the trial:
        realdir = ['left', 'right']
        thisdir = np.random.randint(2)
        thiscoh = 0.5

        dots.dir = 180 * (1 - thisdir)
        dots.coherence = thiscoh

        win.callOnFlip(keybd.clock.reset)
        win.callOnFlip(keybd.clearEvents)
        win.callOnFlip(timer.reset)

        nframes = int(config['duration']/dur)
        for ff in range(nframes):
            dots.draw()
            fixation.draw()
            win.flip()
            win.getMovieFrame()
        pass
        fixation.draw()
        t = win.flip()
#        print(t, timer.getTime())
        isi.start(0.5)

#        savestim(win.movieFrames, f'run/trial-{trial}.npz', thiscoh, realdir[thisdir])
        # win.saveMovieFrames(f'dots-{trial}.gif', fps=expinfo['fps'])
        win.movieFrames = []

        isi.complete()
        resp = keybd.getKeys(keyList=['left', 'right'])
        # resp = keybd.waitKeys(0.5, keyList=['left', 'right'], clear=False)
        if len(resp) == 0:
            print('miss!')
        else:
            print(realdir[thisdir], resp[-1].name, resp[-1].rt)
            if resp[-1].name == realdir[thisdir]:
                print('correct')
        # keybd.clearEvents()

    # after all trials done: report some results
    pass
    httpd.stop()


if __name__ == '__main__':
    main()
