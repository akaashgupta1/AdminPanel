__author__ = 'Mewtwo'
import os

def startDay():
    endDay()
    os.startfile('cashiers.py')

def endDay():
    f =open('lock.pid', 'r+')
    a = int(f.readline())
    try:
        os.kill(a, 9)
    except OSError:
        return


