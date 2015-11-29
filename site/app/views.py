﻿from flask import render_template, request, Response
from app import app
import cookies
import requests
import urllib
import math

ipcamProtocol = 'http://'
ipcamAddress = '143.107.235.49:8085'
ipcamWebctl = '/decoder_control.cgi'
ipcamVideostream = '/videostream.cgi'
ipcamUser = 'sel630'
ipcamPasswd = 'sel630'
ipcamResolution = '32'
ipcamRate = '0'
ipcamCommands = {'up': 2, 'down': 0, 'left': 6, 'right': 4}
diagonal_correction = 0.707


@app.route('/')
@app.route('/index/')
def index():
    return render_template("index.html")


@app.route('/camposition/', methods=['GET', 'POST'])
def camposition():
    yaw = float(request.args['yaw'])
    pitch = float(request.args['pitch'])

    if yaw >= 100 or yaw <= -100:
        return 'Invalid yaw'

    if pitch >= 80 or pitch <= -15:
        return 'Invalid pitch'

    posyaw = cookies.getFromSession('yaw', 0.0)
    pospitch = cookies.getFromSession('pitch', 0.0)

    movementx = int(yaw - posyaw)
    movementy = int(pitch - pospitch)

    # -22.5, 22.5, 67.5, 112.5, 157.2
    # -0.392, 0.392, 1.178, 1.963, 2.743
    movement = math.sqrt(movementx ** 2 + movementy ** 2)
    movedir = math.atan2(movementy, movementx)

    print 'r: ', movement, " theta: ", movedir
    if movement > 3:
        if movedir > -0.392 and movedir <= 0.392:
            # move right
            movecamera(6, movement)
        elif movedir > 0.392 and movedir <= 1.178:
            # move right up
            movecamera(93, diagonal_correction * movement)
        elif movedir > 1.178 and movedir <= 1.963:
            # move up
            movecamera(2, movement)
        elif movedir > 1.963 and movedir <= 2.743:
            # move left up
            movecamera(92, diagonal_correction * movement)
        elif movedir < -0.392 and movedir >= -1.178:
            # move right down
            movecamera(91, diagonal_correction * movement)
        elif movedir < -1.178 and movedir >= -1.963:
            # move down
            movecamera(0, movement)
        elif movedir < -1.963 and movedir >= -2.743:
            # move left down
            movecamera(90, diagonal_correction * movement)
        elif movedir > 2.743 or movedir < -2.743:
            # move left
            movecamera(4, movement)
        else:
            return 'No movement'

    pitch = movement * math.sin(movedir)
    yaw = movement * math.cos(movedir)

    cookies.setToSession('yaw', posyaw + yaw)
    cookies.setToSession('pitch', pospitch + pitch)

    return 'ACK'


@app.route('/camposition/set_zero/')
def campositionSetzero():
    cookies.setToSession('yaw', 0.0)
    cookies.setToSession('pitch', 0.0)
    return 'ACK'


@app.route('/camposition/cam_step/', methods=['GET', 'POST'])
def camstep():
    cmd = int(request.args['move'])
    movecamera(cmd, 5)
    return 'ACK'


def movecamera(cmd, degree):
    requests.get(ipcamProtocol + ipcamAddress + ipcamWebctl,
                 {'user': ipcamUser,
                  'pwd': ipcamPasswd,
                  'command': cmd,
                  'onestep': 1,
                  'degree': degree})


@app.route('/camerastream/')
def camerastream():
    return render_template("camerastream.html")


@app.route('/camstream/')
def camstream():
    url = "%(protocol)s%(address)s%(cgi)s?user=%(user)s&pwd=%(pwd)s&resolution\
=%(resolution)s&rate=%(rate)s" % {'protocol': ipcamProtocol,
                                  'address': ipcamAddress,
                                  'cgi': ipcamVideostream,
                                  'user': ipcamUser,
                                  'pwd': ipcamPasswd,
                                  'resolution': ipcamResolution,
                                  'rate': ipcamRate}
    print url
    ws = urllib.urlopen(url)

    def stream():

        while(True):
            res = ""

            s = ws.readline()
            res = res + s

            s = ws.readline()
            res = res + s

            s = ws.readline()
            res = res + s

            length = int(s.split(':')[1].strip())

            s = ws.readline()
            res = res + s

            s = ws.read(length)
            res = res + s

            s = ws.readline()
            res = res + s

            yield res

    return Response(
        stream(),
        mimetype="multipart/x-mixed-replace; boundary=ipcamera")


@app.route('/about/')
def about():
    return render_template("about.html")





