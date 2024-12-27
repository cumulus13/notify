#!/usr/bin/env python2
from __future__ import print_function
import sys, os
import ctraceback
sys.excepthook = ctraceback.CTraceback
import argparse
from configset import configset
import pushbullet as PB
#import sendgrowl
from gntplib import Publisher, Resource
# if os.environ.get('DEBUG') or os.environ.get('DEBUG_SERVER'):
from pydebugger.debug import debug
# else:
#     def debug(*args, **kwargs):
#         return ''
from make_colors import make_colors
import argparse
import traceback
import requests
import re
import json
from multiprocessing import Process
if sys.platform == 'win32':
    import winsound
else:
    try:
        from . import winsound_linux as winsound
    except:
        import winsound_linux as winsound
from datetime import datetime
import socket
import bitmath
import mimetypes

#sys.exc_info = traceback.format_exception
SYSLOGX = False
try:
    from . import syslogx
    SYSLOGX = True
except:
    try:
        import syslogx
    except:
        pass

class notify(object):

    '''
        Notification handle suport Growl, NMD, NTFY, Pushbullet, Local notification
    '''

    title = ""
    app = ""
    event = ""
    message = ""
    host = "127.0.0.1"
    port = 23053
    timeout = 10
    icon = None
    active_growl = False
    active_pushbullet = False
    active_nmd = False
    active_ntfy = False
    pushbullet_api = False
    nmd_api = False
    gntp_callback = None
    ntfy_server = None
    sticky = False
    syslog = False
    syslog_server = []
    server_as_router = False
    priority = 0

    event = []
    ntfy_icon = ""
    logfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "notify.log")

    configname = os.path.join(os.path.dirname(__file__), 'notify.ini')
    if os.path.isfile('notify.ini'):
        configname = 'notify.ini'
    try:
        conf = configset(configname)
    except:
        conf = configset.configset(configname)

    def __init__(self, app, event = None, title = None, message = None, host = None, port = None, timeout = None, icon = None, active_pushbullet = True, active_growl    = True, active_nmd = True, pushbullet_api = None, nmd_api = None, direct_run = False, callback = None, gntp_callback = None, active_ntfy = True, ntfy_server = None, sticky = False, priority = None, ntfy_icon = '', syslog = True, syslog_server = [], debugx = False, server_host = None, server_port = None, to_server_only = None, message_color = None, syslog_severity = None, syslog_facility = None, **kwargs):
        super(notify, self)
        self.title = title or 'xnotify'
        notify.title = title or notify.title
        debug(self_title = self.title)
        
        self.app = app or 'xnotify'
        debug(self_app = self.app)
        notify.app = app or 'xnotify'
        
        if isinstance(event, str) and event:
            notify.event.append(event)
        elif isinstance(event, list) and event:
            notify.event += event
            notify.event = list(set(notify.event))
        
        self.event = notify.event or []
        debug(self_event = self.event)
        
        self.message = message or notify.message
        debug(self_message = self.message)
        
        self.host = host or notify.host
        self.port = port or notify.port
        self.timeout = timeout or notify.timeout
        self.icon = icon or notify.icon
        self.active_growl = active_growl or self.conf.get_config('service', 'growl', '1') or notify.active_growl
        self.active_pushbullet = active_pushbullet or self.conf.get_config('service', 'pushbullet', '1') or notify.active_pushbullet
        self.active_nmd = active_nmd or self.conf.get_config('service', 'nmd', '1') or notify.active_nmd
        self.active_ntfy = active_ntfy or notify.active_ntfy
        self.pushbullet_api = pushbullet_api or notify.pushbullet_api or self.conf.get_config('pushbullet', 'api')
        self.nmd_api = nmd_api or notify.nmd_api or self.conf.get_config('nmd', 'api')
        self.gntp_callback = gntp_callback or notify.gntp_callback
        self.ntfy_server = ntfy_server or notify.ntfy_server
        self.sticky = sticky or notify.sticky or self.conf.get_config('growl', 'sticky') or False
        self.priority = priority or notify.priority or self.conf.get_config('growl', 'priority') or None
        self.ntfy_icon = ntfy_icon or notify.ntfy_icon
        self.syslog = syslog or notify.syslog
        self.syslog_server = syslog_server or notify.syslog_server or ['127.0.0.1:514']

        self.configname = os.path.join(os.path.dirname(__file__), 'notify.ini')
        if os.path.isfile('notify.ini'): self.configname = 'notify.ini'

        try:
            self.conf = configset(self.configname)
        except:                
            #from importlib import util
            #spec = util.spec_from_file_location("configset", os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "configset\\configset.py"))
            #configset = util.module_from_spec(spec)
            #sys.modules['configset'] = configset
            #spec.loader.exec_module(configset)
            self.logger(str(traceback.format_exc()), 'error')
            self.conf = configset.configset(self.configname)
        
        if self.title and self.message and self.app and self.event:
            debug(self_app = self.app)
            self.send(self.app, self.event, self.title, self.message, self.event, self.host, self.port, self.timeout, self.icon, self.pushbullet_api, self.nmd_api, self.active_growl, self.active_pushbullet, self.active_nmd, self.active_ntfy, debugx, callback, self.gntp_callback, self.ntfy_server, self.sticky, self.priority, self.ntfy_icon, self.syslog, self.syslog_server, server_host, server_port, to_server_only, message_color, syslog_severity, syslog_facility, **kwargs)
            
        debug(self_app = self.app)
        debug(self_icon = self.icon)

    @classmethod
    def logger(self, message, status="info"):
        #logfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.basename(self.conf.configname).split(".")[0] + ".log")
        logfile = self.logfile or os.path.join(os.path.dirname(os.path.realpath(__file__)), "notify.log")
        if not os.path.isfile(logfile):
            lf = open(logfile, 'wb')
            lf.close()
        real_size = bitmath.getsize(logfile).kB.value
        max_size = self.conf.get_config("LOG", 'max_size')
        debug(max_size = max_size)
        if max_size:
            debug(is_max_size = True)
            try:
                max_size = bitmath.parse_string_unsafe(max_size).kB.value
            except:
                max_size = 0
            if real_size > max_size:
                try:
                    os.remove(logfile)
                except:
                    print("ERROR: [remove logfile]:", traceback.format_exc())
                try:
                    lf = open(logfile, 'wb')
                    lf.close()
                except:
                    print("ERROR: [renew logfile]:", traceback.format_exc())


        str_format = datetime.strftime(datetime.now(), "%Y/%m/%d %H:%M:%S.%f") + " - [{}] {}".format(status, message) + "\n"
        with open(logfile, 'ab') as ff:
            if sys.version_info.major == 3:
                ff.write(bytes(str_format, encoding='utf-8'))
            else:
                ff.write(str_format)

    @classmethod
    def register(self, app, event, iconpath, timeout=20):
        '''
            Growl only
        '''        
        debug(app = app)
        debug(event = event)
        debug(iconpath = iconpath)
        debug(timeout = timeout)

        host = self.host or '127.0.0.1'
        port = self.port or 23053

        publisher = Publisher(app, event, host = self.host, port = self.port, icon = iconpath, timeout = timeout)
        publisher.register()
        # try:
        #     s = sendgrowl.growl(app, event, iconpath, timeout = timeout)
        # except:
        #     self.logger(str(traceback.format_exc()), 'error')
        # try:
        #     s.register()
        # except:
        #     self.logger(str(traceback.format_exc()), 'error')

    @classmethod
    def set_config(cls, configfile):
        if os.path.isfile(configfile):
            cls.conf = configset(configfile)
            return cls.conf

    @classmethod
    def _ntfy(self, data, **kwargs):
        debug(server = kwargs.get('server'))
        if kwargs.get('server'):
            if isinstance(kwargs.get('server'), list):
                for i in kwargs.get('server'):
                    if not 'http' == i[:4]:
                        i = 'http://' + i
                    try:
                        a = requests.post(i, data = data)
                        debug(a = a)
                        debug(content = a.content)
                    except requests.exceptions.ConnectionError:
                        return False
                    except:
                        self.logger(str(traceback.format_exc()), 'error')
                        print(traceback.format_exc())
                        return False
            else:
                try:
                    a = requests.post(kwargs.get('server'), data = data)
                    debug(a = a)
                    debug(content = a.content)                
                except requests.exceptions.ConnectionError:
                    print(make_colors("[NTFY]", 'lw', 'm') + " " + make_colors('No Internet Connection !', 'lw', 'r'))
                    return False
                except:
                    self.logger(str(traceback.format_exc()), 'error')
                    print(traceback.format_exc())
                    return False
        return True

    @classmethod
    def ntfy(self, app, title, message, icon = None, server = None, priority = None, tags = [], click = None, attach = None, action = None, email = None, filename = None):
        url = server or self.ntfy_server or self.conf.get_config('ntfy', 'server') or 'https://ntfy.sh/'
        debug(url = url)
        if "," in url:
            url = str(url).split(",")
            url = [i.strip() for i in url]
        debug(url = url)
        icon = icon or self.conf.get_config('ntfy', 'icon')
        if icon:
            debug(check_icon = icon[:4])
            if not 'http' == icon[:4]:
                print(make_colors("[ntfy] Invalid Icon, icon must url"))
                icon = None
        if tags:
            if not isinstance(tags, list):
                tags = [str(tags)]
        data = json.dumps(
            {
                'topic': app,
                'message': message,
                'title': title,
                'tags': tags,
                'priority': priority,
                'attach': attach,
                'filename': filename,
                'click': click,
                'action': action,
                'icon': icon,
            }
        )
        debug(data = data)
        try:
            a = self._ntfy(data, app = app, title = title, message = message, icon = icon, priority = priority, tags = tags, click = click, attach = attach, action = action, email = email, filename = filename, server = url)
        except:
            print(make_colors("send to ntfy ERROR !, see log file.", 'lw', 'r') + " " + make_colors("'{}'".format(self.logfile), 'lc'))
            self.logger(str(traceback.format_exc()), 'error')
            print(traceback.format_exc())
            return None
        #a = requests.post(url, data = data)
        #debug(a = a)
        #debug(content = a.content)
        return a

    @classmethod
    def makeicon(self, path=None, stricon = None): # return str file path
        if os.getenv('DEBUG_EXTRA'): print("path:", path)
        if stricon:
            if os.path.isfile(stricon):
                if not "image" in mimetypes.guess_type(path)[0]:
                    stricon = None
            elif not len(stricon) > 200:
                stricon = None
        if not path and not stricon:
            imgfile = os.path.realpath(os.path.join(os.path.dirname(__file__), 'growl.png'))
            if os.getenv('DEBUG_EXTRA'): print("imgfile:", imgfile)
            if os.path.isfile(imgfile):
                return imgfile
        else:
            if os.path.isdir(path):
                imgfile = os.path.join(path, 'growl.png')
            elif os.path.isfile(path):
                if "image" in mimetypes.guess_type(path)[0]:
                    return os.path.realpath(path)
            #else:
                #if path:
                    #imgfile = os.path.join(path, 'growl.png')
                #else:
                    #imgfile = os.path.abspath(os.path.join(os.path.dirname(__file__), 'growl.png'))
                #if os.path.isfile(imgfile):
                    #if "image" in mimetypes.guess_type(imgfile)[0]:
                        #return imgfile
                    
        
        if not stricon: 
            stricon = """iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAABGdBTUEAAK/INwWK6QAAABl0RVh0
U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAANcpSURBVHja7L0JtCRXeSZ4b2Tmy3wv377U
/mqRSiqh0r6DECCBAcNgPLbVbRYbjI1oGhsvbcZjT59DcWYMp489454z2G7wtPFp42N7MF66G5jB
NhZCCISEFoQQJamkUu37W+rtL/Pe+b+IeyP+e+NGvnxVpRJVlSFF5fIyIyNu/N+/L1JrLTpbZ+ts
l+ZW7izBhb29973vFVEUxbuUUpRKpfjRvmf2bnpvjPY1tPeZvUZfr7BDzSul5kkgzNB+il4fp9fH
ICCazaawj/RevNvXn//85zs3ocMAOtsrtVlwYgPYzfPLab+SQL6FHjfTvsYwgCH6jGUA3ez+N+h7
DWIeYACnCeAT2OkzYAD76O8v0eMLtO/G3y34sXe2DgPobD8CDIDAegvt1xNwbyAggwFcBvAD6NAI
uHaAHZt9xIZjWEbCP2PeO2YYwB7an6bffIL2J+m3DnXuwIW9yY4P4MLdPvrRj14+Pz//utOnT99E
kv0WAvhO2vvK5XIMdjxCK8BzbhJYE4FvVq3HbtV8q/Jbad9oNOLXy8vLu+nxye7u7ifp89/43Oc+
943O3egwgAvjgpnU+1HdVronv/Irv3IFgfunKpXKG7q6um6ZmJgYpT0GOr2Xgh+Pdregt8+LNADL
ADj4DegdJjAwMCD6+/ubi4uLTywsLDw0NTX1pc9//vP/34W+9u2sf4cBdBjAK0KAH/jAByrVavX9
BOKfqNVqryeQp9L++PHjgjSBlAHg0Zf+VrX3pX+ICVhGYAGPRzAAMIK+vj4xNjaWMoSlpSUxOzv7
JGkjX9q7d++f33///T/sMICOD+CCZw4WMBw4FlR2BwABNvvId5LOzmv+WbvzY9ljh7af//mfv56O
94v09CfoM1u42o6NpHHMAPAezhXAtE5Be+78WtplACHvPxgA/zyORwwJ/oerxsfHr3/729/+F1/6
0pf+0j/+Rz7ykfRYIcZiH7FbxmJf4zl/D8/tzjUTfp58vxTB3WEA5xD8XJJyG9sHP0CP1yuBnwOf
gz8kne+99963kr39IfrbO+hlyYIT52XVdPwewIFj47Vv8/vOvRATsOAIMQEOLvyWzxTwSNdXpfN8
e71e3/KWt7xlE2kDf7B79+4GX1PL4Ox58nPxtRSfcflMzGdmPCqB8wldGz7fYQIdBrAiM2gX/CtJ
fV/ih6Q+J25/e+c73/kOAtWv09/vtgSO71kCtwQ9NzcnyB6PpaNlIq2O24oBFGkEVhuYnJwUPT09
QWchHokBXEPn8Svr1q3r3rx58yf37dvX8IGOY7GwZeH5+cyr1Wv/ux0m0GEAq5b+7YA/JPV9DSAE
fg76dlRykqKvI/D/W3p6N1Rcu0HSA2w4llX1Dx06JKanp4PHPFPb21ed7X7w4EGxadOmXMSARwvo
vMfJLPilsbGxWfr6/17EZC2zwrGwRq0YQYgBhD7P16rDBDoM4JyDn4Pbgp8zgSJbP6TW+p54+/o1
r3nN2qGhoY/Sd98aksos/i+OHj0qDh8+fN7WDMwGwFq7dq3gvgjuk8A2MDAwTszqA6QFPE9awD+E
tAwf0FYrKPKFFN03fwMTsL/VYQIt1vFSjwKEJAwPmZ2p5OehuFA83k/bxeMf//Efy9tuu62+Zs2a
q4hof5OO8w76bo/vL7DnOD8/H3v/T5w44djv58tEQiRgdHQU0j6XQ2AdfDMzM2Jqaupb9LXfoteP
fOc731n88Ic/rH3fQpE2YTUKu1unIHcOcichdxDa77dyDIbWqxMGvASdfdxm5t5+eNbPwznJO+64
o5ck5rUE+tcSM7mHCPf19KcaZxxWKgJUsMOxgwm8EkRr1wzgJ00lzgvo7e11NAILQGIADQLmo4OD
g39Nf3vw2LFjP3z00Udn9Xk6afgrrMbEtRQ/QtBhAJcgAwg5zLjkB8heTuDfc889hJvea+g+IKnn
bgLSTfR85NSpUzzzLpZwAPvs7Gy8h/Lwz+e99NcRa1av12MmUK1WERZMNSAwLDCKdevWHSVm8OjC
wsLXaH0fIA1i95YtW2Y//vGPq5fzXHFO3EnJge+bBx0GcAkygKI4Pwj45MmTL9d5lN7+9rdfTWB5
M/3WGwkgtxGARvD7Bw4cEI888kgMdC757Xm2umfnywRo9X4oj+Cqq64St956a/weaVVgBN+i9f3n
/v7+r2/btm03MYGll+t8oZ0UmQMdBnCJM4BQ+Sy33UldPde/H/34j//4RpL2ryd1/+2kFr+efmsd
/mR/HwyAVGSozo6G0mprdR9xDEhk66vg0Qi7QcvAMaBpcLt6tUyAO9c4yK655hpxyy23cEmsicGh
0vBB2r9CzO/rb37zmw/fe++957zEcHh4OPUJ2N/nztRLmQF0ogAFjj8LknO5jYyMVN761rfeSozl
J/v6+t5G4L+SiK0CoHGgQ2XFDjMABNqO5Pe/a3fYv9ihglsmwKMSduNpvcgnwA4NBPkF2PEcqjx2
/K2ddbUgg2mA3YLLMA9J57SFzmMtMZtrSSu49otf/OLf/+AHP3iCtIGFc7nuuFbf8ReS/Jck/V/q
GgAAYe1+rvpbj/7+/fvPia1/1113rSUQvJFA+DPECO6m5wMAIMBlw17cBHn66afF7t274xAfBxSX
6hbkxEjiVGBToBO/h+cAfEi6+Wvge8T93wJjgDMU4McjNBP4RpB3YN/n2gI3BcB8tm7dGmsAOE8/
aQifxWcWFhZO0XH+hd77GzrvB8gsOHKufAPr1q1zIgn893nOQMcEuAQZAFRi3+7ncfy9e/eeta3/
hje84WpI/aGhoZ+ifSf9ZgW/CQKEY89PBbax8D179sQmCEAGQsXfAWoLfAt4eOFxHSFwt2Mu8O8V
ecVDx0UFIpiA3cEIwNBsDB5aB9Tv8fFxaD8O8PhzfA7XTJrAImkaTxEz+Du61n944xvf+Ox99923
fLb3fOPGjWmIkIcX8dshM6fDAC4hBgBAWfD5KbtgAgDhWfxWmST/64nAf5aA8DZS+9fRcSMLdBvL
9k0P7o/A/QGTAAHjXO35+pI2JLlXurdnEgJrlUJscxNgIuA9rB8iAn5+gB/rx2fwWRPxaBITOUBM
4Mu0Fn+9c+fOh8/WJNi8eXMwPwB7yJzp+AAuMYbg9c8LOslWu61du7aHJP87iLjfPTo6+kZSc+uh
JhxFhS280g4qMv8bt1/bAfxKQLe/Y8+nldT3/86ZDp5bzcm/zlaMBEDE98wxS/AN0Fq9h7SBsSef
fHLo93//9//xN3/zN2fP9F7Ye+oXN53N/e0wgItk88Hv72di71999dXD27dv/2lSy989Njb2GiLu
Cic6Cxw/dTYEUgu0VkAvUulDiS7tMAlfo/BBHtIE2i0xDvkbLIPg50BMpJ8Y3zuICfQ/8MAD/S++
+OJ/W7NmzdSZ+AU4+O1z+9hhAB0NICj5W9XmtwL/VVddtWZwcPBdZKO/h8B/s2TIKMr9L+rMsxKo
fJD7oAoBuF0m4jMS/uhrCH6VH3/fT7rhHviQNuFdH8qL30gmQe9LL71UJ2bwt5/4xCeOr5YJ8Ptp
mbCtRuwwgEt8K7K9i8poW4F/x44d6wn8P1+v1989MjJybQh8IcnpS0euMheBnD8v0g7a8fj7QC9i
CL6J4F/PSo8c2Pa5n59fcNwSmVF30Ge7jh07VqPXf01MYFURgpCJ12EAHQYQ9AGsVKJbBP5t27aN
9ff3v4/U1vcMDAzsBHHDFubSjUvRkCTlAOOA9HPXudrcLph9IK4k9UPHD5kCFkj+9YQSmELMrk1H
Y0RM4OZmsxkdOnRIkkX1F6vRBPwKT7vOHQbQYQDBfnmrYQAA/+WXXz5GoP85Av+7SQPY2YqYiwDh
N/jwHWitClh80HM1N6RttNIkVvoMZ2L2d+BZL6qq9IutQj0GWvkk2KOs1Wo3zczM6L179zYWFhb+
ul0mUNTareMD6DCAwnZT7YJ/69atw2Sn/rSR/Ne0KjcNHZu39/KJ369cs+eJ3IDHHnssDgm++tWv
dppqWML2GUe7GkCRH4Jfk1Wjv/Wtb8Vhv507d4o1a9bktJ2iXgv+efiSuMg/YVqf3bi4uNggTWCO
Xv89MYFT7TIBm3thGUAnG7DDAHIaQDvSyYKfpH2dQPhjZPP/XG9v77X+cI2VwOdLT98+tsewz2FS
IOHmq1/9aprDDuCR+VGo6rfb+qtIAwh9FmFJ1Cvs27cvfu+BBx4Qr3vd6+JMP7+0OiSBQ+vDmd0K
5xzROtxEGsC7jxw5Mk3P0Yp8qtU9DjHhjglgFvNiluqtGkgWfZYTfisJQTZpZWho6NUk/d9HDOB6
JP34YCnyK3Bi5w0vbFdc+5p3xcXnIfFRJWiZga1WDCW48K67/t/8ZJyiISChY9rCIqQC23PAe9//
/vfjz/DGHKEmHaGU3KKQZQvNBJmUt9Dx33Pw4MHbPvShD9Xa+V4rbaQd+uloABfQtlKzydWo5ajg
o4dBkczcg7gdIyl4Bb2P3P7tRIy1lX6XMxSuflpJzlV23wSw54g0W3QA4ok2RRVtvhe+nay/kOT3
TRqb6GOdnHZDGjBSg1H0E9ICQo88fNiqRDeUR4D5hvT8TUePHt3y9NNP3/+5z33uOWI0x+lPL9KO
9M1J+rvyGW6r+97qHnYYwEXsAyiSFM8///wA/f1V9PRGAvwt4+PjrxkdHd1In+kiFbSLwICKNgfg
ocaWPph4BiA2SEj/776pgONC7QYA+Ybft2ZEqE9eO1WE7YQY/XPDbAD/XFC9CO3AzxnwGQF/bYux
Qp16isKnrD15D2lh19N+3VVXXbVE67BEDPLg/v37HyJm+Sh953H6+DOXX375lM9YLmap3mEAZ6E1
vPjii1iT9bTfTER656te9aqf3Lp16+bh4eEu5I1DCqMHH4jH5rmHQFcUv/elG5xpxExywOfPbb9B
SFk85xsKgbjDrpXEb1drCmkAnMlB41i/fr149tlnne9bkyGUDGQB7w8oxRpyM8C/9qJwp/e7ktal
Ojg4WN2wYcNVt91221XEjN67d+/efc8888zf79mz55v0se/Sfnjz5s2NDqV3GEBuI6kBCl1D+50E
qnuvvfbaH7vsssug9kcAKMAHjzdsXzyHqluUT+570HmIryjrz9r5IQ++tbOtxOTMA9WA3GEYkpit
JF2rJKJQRANMEOuBCjtIe25++C25/ZAhXwve4JQ7Qos0ktA18sYeqJi0fhIzvqzr1ltv3U77b7zw
wgsfeOqpp/6RTJQv7Nu3D8zgGJ1/JwTQYQDJdvDgQQD9VlLzf+qmm266l9TJEVspBmKHMwuPIDLs
toS4CPCtnIl+mI5LTx8knNDxHsDOTQz05rfqcMjDvhptoEjlDzEDaEE4l+uvv15873vf447RYOiS
Mz8r7c0kofT6QsyR9/ArOjfuS8G94ePFcN+IIURkAgxfeeWV//qHP/zhmx577LEv0Pn/Ld3zR9at
Wzd5qdP+RVkO3Mru9aQhDHjY+P8DAf8Xb7jhhk1w+NmOOAC9fQ7pj0YY+D7sX5s6zFuF89bhfkVh
yNHIpb+t+Q9FHgAstOCGdPuXf/mX+DOos0cIEN9tZf+38ne04wcIMQIwQLQDh/mBfATMJMCxSf0O
MrFQzQOOYRmaP8HI1xh4m3G/TTiPJmAtcDxbXoxH26DUPodj8IknnjhA5/2f6fD/HT4C2ufbcQJe
lFi52BkAPR+gh2tov5b2deYjaLNzALb+tm3bfvGOO+64ube3t+SD3kr/2dlZTTblIhHaMhF9NxFU
2arlreb+hWoKfK3ASj/bdiskPXFsNP8A6HBeYERWEhdV6a00DqxVVKBI4tod14RcADAhOCGRmASz
COvFB3KEMhwtIwATxXd5Zp6vJfFj8IGiNqyIR/432pdpTQDmCt3PGh0fvgGHAdjndL7Nb3/72999
8cUXwQgwVWUT7WvNKRyh/Snav0+/P9VhABcoA6DHcXr5M3ffffevkE0/TnZfGQB6/vnnl59++ukT
BNZuUmMHrYrvq/xETPrQoUNHyHb8OhFs/8jIyGuI8AeLmofwYSA2Wy5Ux++bAFbNtSDyAYtjgZDh
d8Ax7XmGVP+VtIAziQKEtACckwUVwAfmhXXzfRiB8F38HUh/PzIQmmXIGSXPR+AThXneA713gtbm
2ydPnpwhBvD69evXr6N7hjRiwZmBff3kk09O0nfnd+7cObp9+3aMX4dJ2Hjqqaf2k7b1f9FP/w2d
+/4OA7jAGABtYwTGD33wgx/892QDVgEaDnQu7TnoTTNMTWrtYZJs/42I6x9J6g8QwX6EAIjBHRW/
dRhe+912bSmxffRt2VDYywKJD/i0APHj6CGfw9nMBCzK0S/SAjij5dGBos/zPAK0M7P2v58t6JsC
fO2sT8AC309WMkxgmT77GK37H5N0nyXT7U1kKr2DGMF6un+Sg58zA64h4G94vmfPnsU/+ZM/+d/o
uJ+h0zh+MWLlYnUC4rpe9+Y3v/lXN2/eXLWdbH0V339N4FPE/Y8cP378v9JN/zId4ztEqHAQ/gaB
HQk/lVYACsWvuZecA8QfUMGloyVo7jjj48A5YIrq9c/UB7CSCVAE7iLAc0ZnNRnr+cdrPsq8yHHY
bpKQeV2hz6Db8u0bNmz4P5599tlvEC//Et3Tt42Njf0EaYHriBGgujA3YsxmXtq/gXZAQ1/+8pfh
J8Bsw0aHAVwY2yhx/Z++9dZbR61a7av5vp1/5MiR2f3793+RbvwXAHzaT8D/Rvvb6HN30XHqIDJI
ryL7mQOES/GiBB//e9anAAKE0zEE9qJS4lB7rtVKrNVqAa3AHrpWK13taxv+4+W5PFuSM4AiRuSv
L3Yy3fqImd85PT39L/Tn/0r7l+i3HgYjOHHixL3j4+M/vW7dujqff8DTrvnMQdDQo48++tOkDX7T
+AY6DOAC2Ma3bt16G0DUjspP4J85cODAp+l7/4n2/USoiv6G5p3biADvxvGIqEpW9YQtbmv9bZsp
HrriwG9l8/vS337GJhhxJ58P1FbAL/IHtAP6s2UEoR2/D4efvS7/2q3Tr6jPIC+K8pkp33FPEU0h
8JcJ8Jvp62+kYz9Gn32B7ukxNBqle/jUCy+8cIg++8vEBHpDQ0a5FgCmBVoiBjDeYQAXztZPAK2D
GIpAb30CJsQ3Q9/5Bt3sl6wtC4FF+6uJsO6gxx4LXNv2Gp+BNmDj8n71Ht+K8vxDITIrCW1M3WoC
oWq6UMptO12IWoW8VooEtLLvQ8DEbwNEfIJwyEzyHYGcObRaO2wmUhOD3zJp+kwf/elO2qEFHKD3
Fkn7UHT8l+ief4PW9f30nV4bTeAmgckfSJkBaAk0dbHayhfjNj01NTUDggjZ/Rb8dqe/T0DltyEs
dJ5Bnw96fg89biRiijghWkZgHU/QCEDgK7XyCjW/DEl1a//bvHr8ls8EfGnZSgs4k0SgdsHfSiPA
mtmJRDwBqCihxzIBfq2+ScPzA3DvYOLZCASvdIT/lT4PLeBN9N3HCMjPk6amzZogUjBB67ouNHLc
9w+AlkBTHQZw4Wxkzu9/+LLLLtuOG2ilfwj8hgE8hu8w4qzBiUTEcgs9VouI3Upo/AaO6/ftD6n/
rYpcuC/Agtrm/uMaeNJPSPq30gJW4wNoJx+giBnYNYRmhFwB2++/KDzIN8skfB8AvxZbcmzzJnj9
QcAfAL/N7bTfSH/aBy3A3Jv9uOf0/Vf54PdNAqw7aAnf6TCAC2c7MT09/ffPPPPMm9bSFgK9vcFE
SIfQWQbfMQQKCtyCaV70uIneKxW18PYZgS0WsqOxba/7EHB8r7efBcelt62Yw25j7e1K/1ZmQLvZ
gKvVAsC0IPmtn6SoxqGotZmNfPCQoAWlvZecqbQ4FzhntiAiRDtAvA9DSXGvcc9JQ7ybmNQGP7MQ
v4VrwONR2kBLxincYQAXyIZwzdf37NnzaSKC30bZqA98Q1AzRFB/hM+Cxsx3YfvfTDukRhcnVD/N
1S/vxaM1OWxaME8N5l59Gx60jCDUqJJLeHwfEhV/50lAq5H+K2UCnq0WgM06+7hjz3d6FnUc8h1/
Vq239y2UHVh0Hkzr6qZj3UrvXy+SjL8lc6+/bu79/0z00RsyBSYmJuZeeOGFTxv6aHQYwAW00Q0/
Tjf+vxATmO/v77+PgAhJUDXq+gI9wuH3J/Qewn7HLUYQQqTv3YFGv3x9iqSjBSJXXy0B2go/3sEH
ksUmwfhxfc4IiiQjAGZLiK1JUKQFrBb0K0UFWmkBuCabUNMqVFgUyrPrwDsJWZ+MZYz+8Yq0AO86
sdjbaYcz91vsXuPxzw0tfBD0Qedew2+SFrcI+iDJ/1nQh6El0WEAF9Bmbhia1v1nupFQ/64TWa43
agFQxvZ92ic9YoGkuEEkOQC5yr5Q591Q/r4vnewQShvrxw5mYBNjuPQPFc/w9232IZ/DV9Rrr10/
wErAL9ICrLMSOx/D3SrngXc64hIX18Lt+VCbtnbDkN6GKM4ttKNj84NMmsf0QefzMP32dbQH6eNi
bhxyKZQDT5qb/mAbn+2hm32bkRjlIulp4/28xzx33hXFwq0Ty5Ya2z71liFYpsDzClr1MrT5CNYu
biX9z4QBtJL+MbdkFXcrhQd5ujN3tHFJX8TIQ5EBnmFZ9LssEoMTvMqYdmgMcroVfXSGg1746v9K
mkFog/jdYaT/sDEHgmE93/a3DitLlEX2rn8O9nOcIVgJ75cZ27JZP93XmhQ21BnqMnyuIwG25Na3
9f3rtmFS3hzUVvAVMYnQmqc3KDBc1U8OCmke1rQzDACm4NP4s+hsnYYgbKsZ9f8KEeiWzAterITm
jryiCAFnHJyAQ5OBufMLOzcNeKUhLzm2xUdQwcEIeKXgaqMAK0UC7O9wdZ/X6PMuxCwhJwj0VgNP
inwZfvNTXiAUysHwNph36P2AsvDnaV/okHyHAXAJsQZxf5HUhQenglpi9qUsL/v1idf3/K/UjLJo
UKZ1KvrfDw02tV17eYORdhlAiAlYJ6bVcmznHbuvJjmoqHaAvw4MCW3ZUIW3OQ8VCzFah/S/ifav
dRhAhwHwDeG+a4yE6C4CJTYLfjxa0FnJ5CethGLzRROBiwp9QozFzxmwYC/yAazkgS/yG3AmZo8f
Ct2daaZgka/EHxJSpKmEugUVmRNmqxsN4EraT4qLNLTXYQCr3+AlvomIZouZAVBoi1rw8xBUUT2+
78gqAng774UAHar/t4AwDU1ik8Cq4yuAw/kd65yEnY/Qo/VFFHU7bgf47TCDUKFUkeTnTtVWvgS2
QbO73Ph50DJ8psMAOhsAP240gLXc+VfkuLOPvB9/q+GYrVT8Imnfqt7fzzcAAJAWa/sehKoFuf9h
pYEYFohgIrYTsj0mGAKiDzYpaSUt4EwZwUqfCf1OyGEbYAAbjK8HTsHZS90Z2GEAifPvatova2c9
ziTPPiTZQ+aF/zqU8suZjyl9TRmR9QXw4RuhicetGIBvn/uPNh0XI8ngF7DMgOcAtMME2q0uXE1C
UZtaQJcxARDxOSiyDNAOA7hEnX+9IkkQwTAQGRqo6WsCK1XztTIhVgt+/txKZQwI5Ta/TSbym5H6
jUmLOhT718lbcHFPu/+I3bZKBzPwpwWdrSbQzndCEYsVmHNkHL3Q+B7qMICO+r/ROP9GffW/Vbut
lWLWZ2Ln+6/5I1RxAJ/b6HznoUE/TGht91C/vSLp7w8Q9Xvv8SiA3TEaDL+BPgl8gtHZALtd8LfI
Agzd87VG61tj/AC6wwAuXfUfqiDqxiut1H0/1h8CfKgRRztz+YpUfmxQt+3UGx7u8zsS+63J/ZwB
v0V5KFmIg8hK+dBUX96WOzRFGOfLMxX9JKpz4TcIgX8VW9WYfMj43HcpawGXMgOw6v8OIwkKVfNW
nXZ8ALVjz7ej8gNUcOrZxCO78yxBW0vAU4l9BuCDP6QBFCXqcA2Ajy4PNdMMMQScP37fFjC1AnW7
dv1KBUqruPcbzL3/VocBXLoMAG2eUPU3JLzU31CF3Zk22liJWfhFRHYSkT94hBcQ2ek3lgHYAaJ+
hqDfWKPdKEAowYYzAp8B+OXWPiOw59tKbW/XsXeW4Lf3fsTce4SApzsM4NK0/8eM86++Go//mVTc
reTgwwaw2Ok6XL238XgLfMsELPjtZ4uiAEURiFYMIF4gY/bweYY4R3teOE/bOIM367CPlknYmn48
Wt/A2Uj5VnUWq2AA6Bk4bnw/Ry9VP8ClzAAQE8aosEFRkPrbKgLQjg9gNUwBYLIxfK7S26IbzgD8
RiNc4vsx/zMBig+2UJsuXp/AmRWAbmsSsOMznBGAwdkORyuBu11GcBa0P2zMvx+KSzQr8FJmABUD
/tpqQNEuEygKC4betxVzthKQq/l854zBV/PPEShafp9nPtpIRKpOMe3Dj0DY960WAGZg3wt571u9
d66u02zdhgbKHQbwShniZ9ls4SwIAajp8m3/M/mtlbSBUMMO+54Nq9kinhDwLfi5R59LUL8b0Zmu
60rgb6UZWeDb0el+LgKvdLT+AZ5avJJtfxb2/kqmQFcrDfDlpt9zfD0XHgN4JS+ebt087ctqled7
Ns5BHg2wYTbeAyAEfB/0fpfdl7NjTTsVg34TDs4MOFA4E7QOQr8HYtHjywB+HSXe/wXl2f+f+MQn
2j7Irl27Vv3DH//4xzsawCu5/YkU3aeGh6/4rtI3fHtmZvTw8nJjeRVrsdpoQFGSkJXc1n727X0r
9f3JOOdC2p8NA1hpNJo9Jxu2bPUdvwNyO4/nYqsSH91arW58/eDA7TubzZd6Tp784Qe1mO+YABcz
8CPZ9eejIztrfX1vGWks/4+1I0dumW40IxSGHzsHwFiNNuCD3/fqc/V4NRL/5VZJ220sys0ca96E
GnjyngXnQeqntt8oKV1XLy9uu/XUyY9tHB9/0/zQ0N/9+cTEV+ZPnnz6UNI5uMMALpbts0SFpWp1
vH/TprfVlPr5aN/eV+PCEf+5UiYVIbM6KQ07E7C0asPdSoLy5B7fvufZeCvF718uLeBcMAKutfBm
JaFio5db6lujH9lfyP9GMcCYapail/beQhrBLbXxLe+cqdf/LPrUp77UXFzcf3jXLt1hABf49hkp
a93Dw7fXe+sfLB07+q8qjWXEoNJAMHJBD5AJOEePB/WZtYkpqhtoxRxCefv+aKxQi/BWBUfn2/5v
x1HYykdgr7/dwSHnAvxw+2+gJ1fQeYzTY5dMwkHwAi4f2HdbT7lyY9fGjXdNT059Zt2uXQ8f2bVr
ocMALtDtT3t7R3vXrPmJmta/2nXowHUlAB/eafN3uKg2EJHdBOArHS/GSXo+JVafG7oSsXJGEGrj
5c++a3e45/loWb1aTSD0Hu/bx6/fOgILmnmesw33GvG+sRj8QtxARLAWzAityUUWEmo0GxW5b++7
BkfXXltev/4/Vn7v9/5h/8c+dqLDAC40e79W21QfGnpf9+zsr3UtzI6KCECToL7EIy3i2l/RR/uV
BH4tlegjItxLtDdB78EcWKDn8AotwmY/h4yAh8n88dcWLO0C/ZVkAKt5v5U2wNcidO1nskGi18ze
LZNUzxE6/jbaryM6uByDSyOz9tjB9NHfkX6/QvQgTx67pq+n7z9EAwPrN3zqU3926Ld/+0CHAVwo
4K9WtxH476sdP/4xUu9KslISspTtJRtSoxtd0koM002/rtEQwySNNje12E/vxZoAEcScMQuWDIEs
G+1gyezNVfoGeCYd936v1ArrldICzoUfwP+b3/PPL1RajUoPoFeM9K7Y5+iRIJKSv176UD+9huQf
p9/ZRvuGEoHfpE5rdICLzH2CloIeCLRXFN3ZmZmRnpmZXWLNmt4Nn/zkZw79zu+82GEAP+oOv2p1
S+/Q0Eerx4//Gggh6iLQw86uVOh5lyiV6REZbCA4AjpuepnAX6GbXqfHDY2mOEXPT9J+gohigpgE
GMGsTmJE8zoB/oLOhswtwZttntsdjKEJQItwmbCvHvPEoB8V1f9cMIPQ30LMruh6IrOXGMjLFuwG
6DHYZQL4moSdL2PQYx8icI/QPkoa4HC5JHpLSFtOBIEmuhCWCaDmAcVOjWWhkKy0vEy/0xByqVmq
HT36W2Lt2tr6T37yDw7/zu+81GEAP6LbH5LaP9Dff1/12LFfq0CqQOIjkaZaFWX0zR8aFtXhYcTg
hEZHHczuw9BJ7MtLMSOo0T7aVGKx2RCLDUWAb4pZej2NOncwAgVmoJKoAb0+HTMGGTOBRWMuLOuE
CTQMI1Dxo6ZdigYKauLkHwMGAAHnioSYcwD485mZdqa+AZyhtj4BlDvDD0Br0g31G0QJS40+VTLA
t+DH+7UU8DIu46vTYy96D9idwN4H8NO9r0PSy5KoliPRRcCX9BrCQCC3otIlZFeyC9Qm4H36zuKp
U2J54hTmsYvm4iIxBRELB3HkyK+qsbG50U996o9OXETmwEXDAP5AyuHhkZF7q5OTvwnwRwz8laEh
0Xf11aLvVVeL2tr1ojk/J9Tp06JBu5qZFo3p06I5OSmap6eFXiAIEzPoIoLsw8gq0ghApA3ksKM3
PzGDZWIKSxgJTszgNKmKMyrREOYUTAYwBB1rCgtGO7DMIH5EXz0U/tD3GnJJKJI+TUh+WCT0HMxC
QyUV1jbVwsJGGltVxw4MmaavJe9Fznv2fQs4+7dY0zC7lbDJ95PfazlVyALYHkNkedTx8djfuZrO
Px/BzrY7XkMDozOo0mPskadrL8eEaaQ7GpEKzGwD+BOQ90TJYy/ATpK9Ro9ddM+76DnufRk7tDzQ
AEn7GPAAOEBfq4pSX78oDQ6Kcn+fiHr7RbmPHmkvdfeIhaOHxelnfiBO/+AHQkxMCNz+yGgc3adO
/bvG0NCJpV27/mx6165THQbwI7L9r1LWNgwOvq26uPixilJdkPwRKtR6qqK6bp0YufO1YuDmW0Rt
4yYyAyoxoaolkv7z86I5N0tMYEY0pqZEg7h/Y3KCXhNDmJkVepb+RsxCz86JrqXF2DYU8a6EhLqo
TIssAn6DtAJI92V6Dl/BAj1f0mASpBVInWgI9LfF2HTAY/J8AczEaBPL8EjrRGugsyNmIGOwK4Nm
HWsTMn6tDLr4Z6y2gT9ojwHEQCWgqFq3WKLrFsbUQFE8QqBN+EbqdRHNzSVlvwF7G0e1Knmk7aNy
VPUoZTjmuRYxwAmKCbChqtO19lg7HQDHgFGS0ATPWJXvAqDxHl1YLcJnIlFFbwSZAL1Mfy/Rewmj
j0SJgK9jwEcJ6LF3VYWs94iIQC3pukq9dG29faI8OCTKpAWWBwboda8o9dSF7O5O6ALM5corRc9l
l4vauvXi5DcfhOQXjdmEgZWbza7uhYWPDYyMHJ/ZtesL6iIIEV7wDOCPSGSt7eu7jSTCr3XNza2P
HUpw8JDkB+DXvPXHxcAtt4gu4vikZ9P/icwqE8GJbjIL8L6G84cImUwBAL4J4M/OiOb0NO1GO5ie
ihkFtAexQNb/8qJQ0BagzpPGAOcRxAX8Clrp5JgAElRdgJneU/Rek/4UmwHxcx0DHsxh3jAIMIfE
hABTSUAdawHamhEiPoYy7+PYTWZywKRQVqobqW0ZgKQDluj659aMiVOHDsfnjP7YR9Ddd+tWIQ/u
E4tLC6SJSKEymyKR3OYYCJtZG7wkY54C3ST+e1lae12KyHCBsvkcwF0xj1X6YzfqH2TyHsKzZVmK
zy05ZhRHbGIzwFY7mnsXazok1aHhaZLokO4RSXVRob3WFUvxGNj9A7GUL5GUL/X3i6jemzA4+rtA
wVIpOWZyogkTjRlZNRI927aJMmmNYBbH/t+viLmX9seaG7SW8uzsuv5q9dfV0NA+0gQeOH6BJwtd
8AxAd3Vtq9dqv9R18uTNkbH74eyrrlkjRu65RwzfeScRSHciGURMrazzp6FsJWP7UBDTgLMQBAPn
YOYnwA7AEzhIesZaASTlLB7BLGjH4+mZ+BGahZqbj48R74ATQkvW+w2pqZPXsTZi9qbtxmtALHQC
/NgIMA5FZd8z72ujmSvDHLTWqaqvrKONfk/S70P9FnQdoqdb7F6/Xpw4cED8BH320OWXif5qRSzS
9UGKggHoGNmmv4BtKGJ8DLHqHpskVjOAJ9+E3/g8ArveMmEQkTlWDGprbsS/Zfwf5vfi15FhO1Gy
R3TOsaQmiR319SaPBGgZP5KU70mkfYTP1GqJBgCpbu37yLAwe2wpU/DHTE4m5CCN+VUZGIxpp0nr
1fzSV4QiTUAZH4U8derG+tjYLy12de2nly90GMArtH1Cyv7NIyM/WTpx4uci40iLUFVHAB567WvE
8KtfkxBDiTXDTLGfSMYYPXFEQBuiiGLAaKNJSFIvRRdKR7pT+xmMAeaAdR7qRdIIFvG4IJoLBP5Z
Av/8LGkL8zHjiP0K9Lf088uNWHMQzUasNWgwGWgQKjEv4t/H35X5vRTxRq5rbcU7e9TMTNfxd60W
ok1oK1b78acXnhfRTbeIp4gBoCNKY+N6Uf/GA0meBNaAhUyt9LVgSX2M0oJHZI8yA5SQWYwd341B
iOOA0Ual1EELaS5K1jGXOedEtRbb6wByiUAtugH0blEiZi7pb6JKn8NunXmlJNqT+jGikmEuWe6H
kMzRGiNeG9+IFoZdxZpA/IzOE7QDGlqGefjVfxJLMPugBaBpy7Fj762Pjj4xu2vXZ+d37TrdYQDn
eXu7lNE7+/tvqy4vf6jLNqhAuI+Ipf+aa8TIXa+PuXhMGIb7p8Rr1OLUStaWNSjjok5s14SQzWdA
RCpRuoUp1MGxoU6K7kSSA2RlAziJIhcAvpFFGgQ0iYZlAMvJ6+Uk7ATHY8IMkr+DcYhF0jrs+xbE
KtMeMlDr2FmpdTM+3VTLUImvAuditQdr+8NLbtX68jLrhcEcqDEocY1WBZdWohvnGmMWqRS30Rd8
D6o61PRqAmQL8Bj09AhNLf4dSOpyJfl7uSt+bT30spyEbzU7F2nCuPF5secJ+K2EF6n2kYh2y/2N
2qez11JIx9yJ+YJRaUBDoKXFQ0fExKOPxtEL7DBfeoj2hoeHv/d3u3b98227dqkOAziP2xuE2NDT
1fUuUv2vlFb1J2LqJlt27C1vEbX16xLJbwiTNfw3AOHeauYy497vlDFYT7w2r2R2zJjgsu+lEqic
nI8wCSbCSngO3DgcmbyvTLRBWO0CDALMIzZDGkbraKTfE+Z7VhNpTk2TCTIdmycxc4AGQH+HPW2B
byUyrrtCjMemREek+ttIgWTAigBKgBUS20jSWM2GF32gP5W8sbQtJ173hCFYr7t5jI9TMUyhbI5t
jut8zzCbyLxnmUopSkBqtDzJTAZhtQwrwQ2yU31Pc7XPaHncPao1v6vMHEjSxsnwj2kJNLVw4oSY
ffbZOCIUOwWnpq6ojYz8LNHiM3MoKekwgPOzfUTK6g2Dg3eXpqf/dWTy+0FoXWNjYvSuu0TvlVcy
yVUUF9cu9rmazVVtG4TTIgujCc2eG9KBnc0cZ6l6GT+KTGJZZVMa6VVOJEpkVH+YAHidgLiZSvJE
+uv0MzH4jY8BTKQC8wPRjKNHhZo4ReYHmRwNGZ+3VImEhnREyjPOpbQwn54vnmdqe+RKcQPmUndN
REPDorx2rSj19iYqermUgjIBbWYuOJpDVMpyHexnShzMma2f2ufSy2tgJlyyphF7LpN7YrQ2yaR7
ygByrjrJHjiXcJIq0rUATYG2licmRPPw4cQfQD9YO336Z4dGRr4+vWvXX5V37VrqMIDzsG2rVC7v
LpXe1dVo1FPpT/Za386dYujWW43tnrf7Q9I/4f86zxu09r6jmJ2tjX3u2d/eMdJYekqExswwXMfa
9pIpIpqb0nBINbldzWmVzS2A+mscmHB4LtfrQh/YnzgpIzZk1HGAMoLXMtOQJeveE5niKQJ/adO4
qIyOCUnPU9BzMHHfgEzjDonmIJnpzQGZ9gzQjBNHznUmfpfs+JrnJMQWmoy1HR1ljDc203SUSnTD
GfzG76muILWlAqYF2FOwTIBoCrQ1s2ePWCQmgAgKNKtoebmnW8p3DVQqj84K8YMLDUvRhXbC/07K
7sG+vjdGp079uLTVfUT4PePjYvR1r4uTfmSJSRUnXSUv/TOb2Zf+Im8WsGQXC3zNnXFaO4SdOez4
zqlY5k0QIXLH0NoTYzrcwzqW9mgsQppQLKW5U85fh+Zy9k5zORfx59/FsXDMWOXXBbqU5q+ke+5a
57mjm6bUUhNzjsEcoDpl1IH7oz2u6t0LbRmv9tOmvHWwWgzRFGgLNAZaA81pm5tw8uRbhwcG3kRa
QHeHAbyMGwFebqrVttek/Enr+IP0r/T1iYHrrxd1qP5G1U0KPISwuXTa86an4TUeDeBE5kh/j7BU
gKhSTUAFjuUxBjwaG90lSuVoGi4YVPi1Sr4nmaaCWLnsros0Nqdd/MdPm5nPCs+lR/cpHqLkWEm+
vMoiIVqZdWhxbv66xd/3/habMtpba+FGO7S3tiLArJXOrZvO/X72N5lqAYyR8IpFqxPoJIFKykTr
AY2B1kBzoD1kcSL0SXrRT4I2d+3aJS8kTF1QJsCHhejqq9fvJOl/j7UfoZohcWOEODNU4MR5ZFRY
KzmNfZ7LbtUibcyJHvZNAkKctEJ2byXOG9ABMHLp7xMgV/1dkPrSR3BVlmsG8a5SgMXg4IxHMcJW
LPVWcTOFVFOEyGB7Cw8AKyZWuNITx8CxMtCpJG9CGt+GStSomDEonalV8bIbEEnDYHQpL+l56rHD
GESSbojfk1FmCgjzm5E0v2tVOWPW2HNPzQERr+UyhpM0G3HSVImkOfoulm2YV7rXLyX3M+gsnIhs
SaIx0NrM88+LJcxsRC0DnKonT949MDr62g8vLDwrkpKQDgM419L/P1QqW6tCvLNqHVboPDs4KAau
vVbU1q83IT+TXKJFoOV0BraYKJaXxbFTp8TuvXvF3kOHxcz8vKhVymLzmjXiKlLz1g+PxK+LmQBX
QUPS3zUjtCf5bEjPl/5aeFqF8iUf+x4dRypfs1DG2y4DqnfODRY2j+xTHAPHgrNRJMC3YI/LmwCg
9Jyke85RlDFLaeoPYuYG7EbZ52JNo8RUc+at19LVCKQSaQWDjdJIzX6b2/1I2lwWh0+dFD/cv1/s
O3ZMLCw3RG93t9i6Yb3YsXWrWDM8nAwqscdM5YZx9RpaiunNMAHQGmhubt8+sXjiRJzZCVOgqvU7
t1YqX/utXbue3XWBZAheMAzgbbT0/fX6HdHU1D3W8RVL/y1bxNAddxhPtLH9hcmG5xLBux2LRBi7
974ovvrww+Iw3UQu+XbTjX30h7vFPTfeKG64/DJRR6zfmA0ypPYXSP9UKiqV9zEEHJNW+qeqvWJ2
bFD6u+o1PyeZhj517uJjelas7BhqeI4hZOZRpk1pD+wyOzdfCygZxmu0gMTgVqkW4AI9b6MnjIEk
f6STsu2gFsDCMyl4ZergnSWt7ok9L4ivPf64mJg5zWwgKZ6me//Ys8+KN99+OzGCbaJWrXoLJFIN
0kZ9Er+SjmkNNDf1/e+LpcnJJNcCTGBy8u7BgYFXv+3kyT3iAhk0csH4AG4QYn1PpfKmSrPZZUMz
qOLq37kzTvtNk0NsJheP93rSv0EE/9LhQ+LLD30rA7+3TZB699VHHxHPvPRSHPcVlmC1CDqkgtLf
b4zBiTtNC2bqeyxlGbjNZ7V9Pyf9lcMUrPTPTIxzYY4yFd3mF1impcw5eLZ//J9Ng7Zrr4xmo4ym
4xxHedqQbyKJvC9AhO+FrUrEPcO9wz3EvQwpOrj3oAHQQkM1PZ+NdmwCybIdQWugOdBe2fgCGmhx
RrRZr1R+7JZk5FzHCXgO1f9obb1+TTQ3d7dkzj9I/0GE/VLpL13Pb1D6azE3Ny+efuEFcXxiwiU0
z2t8enZO/IDMg5PT08zbr1LnEXcahaR/ClIODh2Q/tyVzsHMzyck/TV3rrnOsTTIqTMT2dkajfBz
HkLXWbgs75VXLgP0GAM3f7QKRViE66RzmKRy1i79PeGudbrGQrv3hp7inuHe4R4WRnVoAw2AFkAT
OfNH+Eye5QbQDtoDDUqTGRrXOczMvGG0v/86MgGiDgM4R9svC9FXr9VeV5qb22g5cLmnR/RdeaWo
rVuX9flzwl5h6Y99enaGuP4RA+IWzjDaDpCUOEXE5Kvq0iEMLt11gfRnqrov/blGEJD+Gdh86a9c
0BkJ7bglhM7FDRMTIPP8x0lHwbiedi8vPVfOjFRQC4iZUkgL4BLf1wIYUwlqAT4jEdq9Fyyki3uG
exeM8PFcDfoPtACacDW3vBZgezLY3ADQHmgQtGgjAuXZ2Q393d2v/+Wk6XSHAZwL599Yuby5otRd
ZSv9sfjr14v+667Lcv096a8LpD+2peVlMYuy3hbS376eX1gUCyj2YY65fFiRSzOdhbpSAKhC778W
Xjqylf5aOQBMpbzyAK0D/gX7XiDxJT2DJpP65nn2d+2qA5qfjxfu4wxDce2AazWZ6eD+ihcq9LUA
h8kpN/rCwqra0QKSR9wz3Dt+L4u0ANACaCLoBOUMnGkBNgENNBg7oA0NIiQIWgXNXgghwR95BnCF
EKWhev1aefr0LXbhURxSv+wyUd+2Lcv4k1m6WaoAB6Q//qnAeVirrSj98VhDabGNBKTOfj9W3dr+
by39md3O/pZ8XOX9BVz6c63BgCxVm4Vy+Yp/iawAiD/3FYDkaaaSp8zJk+bat+HZ+5rnQLBrTa+/
QAto6QdwnJ5uGBbv457VYuetWFELAC2AJlyGy5OwMprilY5xXgDRIGgxLmwyBUnRxMRNw2QGXHEW
Q0c7DMBsdwsx2FupvLrcbFYtAygPDsaqF9J/hVPsk+aPFkp//K2vu0dsWbeeMQnBzAHtSMxNo6Ni
pK/Pkf7Cl1wOwXhqugnv5ZNSmB9B+MlCKpOiuSiA9772chIEZ1CeXNdixTCgDnwvBVjqVwhENExo
NQW1U2vBE4CE60MR+YShTIvwGYtyGbrvm2D3BvcM9077HF37AkLEtACacDTBkC/AKxqKi6OQgg4z
gGgStBmbAUSr/ZXKa+5ORhFcmGHA89lqWkonV5VrqtEnqtXx0vLyHSXm/IPKhR5/jvQPAJ07jSRz
aNW7a2Lntq1i90svxU6gAj4hyJYTOzePi+F6b1vSX3vSXzppAspx8EnlJe84Ul6kDCSt7BOupJRW
6nKJrFxNRLMahVyiKzMB+HP+eZnzX5hziv0sSUJQ0rhMpmEyadc9Dv8pE5aP3Nz/OEfA1EUomYJX
2jzjmGGUMtM7Bbr0QrEmJ8DmAdgEIdpwz3DvXjh8WEzPz2duIa+mYIyAC1oATWgWPk5XLisK8Eyj
TAsALYImF48fj0OCcAZWiGbXVaswAyZM2CKlb+QI6EDTxVeivftZ5wHcd999Z2vjV2q12ujg4OB4
FEW1paWlxUajMb+8vIy90axUbhezs9da1atEHBdqV3VkxLH90yJQxy4VOfsaO5pGblm7TrztjjvE
P37nO+LQyROpZLBHG+7tFffccH2cEFQuRTk72FYCpjFt4Xn6PfvfzVH30lRXkv65TL9M3smA9Ndm
DZzImdai7VRAxswyAQimI5PEIJEl7Ggh8/kI+FwU0gKS4p00aceW43JTzeYcpI5EKwqiNJHIyQmQ
bP2lSP+Oe4Z7R8QkvvbEk2ICTj4b0ddJ8tCGkVHxY7fdFtNCOYpYFqGnI/G8APy25wsALYImZ559
VjTR3wHXMD19zVJPz109pdJcF23lcrmbHqpKqYXJycn9RPcn6LyXzxZLn/3sZy/cRCBahHJPT8/G
1772tf/L+Pj4Bwj4S9gJ+HOLi4tHG7Ozk3rPnqHy3r1VYZx96OHXe8UVrCZceiZA2POf2bbJ+7Wu
irh6yxYx0t8XJ/4gExDOoGqlIjaPjokdmzaKDcPDcbPKfKpuppJKHrZzEMeB7Up/N4fe85Yz6S+4
zZ3z9qsM7Eb666ZyQ5M5hWpVMkM4hT12b9q2ozIpLWZaQJy4wzP+VCLlc1qAUsJWRCc/JdM8Aa4F
xElD0s/CTKr/kjRhy+xsZqAr3utdVXHT9u1iHd3H3QcOin0njotFAmid1P04E3DzZrF2aFhUTKPY
5FRkViFcoAVI87mU9ogWQZOnHn5YLM/Oxq3d0EC0a8OG3/ixbdt+qdrXN1qpVHqICYARdO3fv/9P
H3zwwd8l+j9Aa/uKJgyVX0HwR7QYI9dff/0HNm7c+AvNZjMi8NfosUaL0k9/W1cnMA4iwcJT//vJ
5nJCf0zVzdRu7WTC6YDNDsfPBuLeawcGxO07dsQdfuNJM2A0pmOOYH38pMjbodrLCuThMT/+L73P
yZzZwfwFnjSWjiYRKHoRXlSA18O38HMKUVgN72TYpdciS6lKmbUCl16EIFHhpeb+hySjLxHyJS8Z
0lsbITJpj5Rhk1acZQ9yX4HRSKS5R7F2kDAFkEaNaGjr2rVi4+ho3NYd+Y+YSViNh8RgOlDJLRe2
ORRMC7DMVKblyUxlNz0MQZOgzfkjR1IzYKTR2NyDpCQz6dl+B/ROdH/4kUce+UN6fVxrrS4pBgCb
n9ShgSuuuOLtO3bs+BgtTgnFOAsLC3FRDopzsGBrp6dFn43lwrtqyn4rBFjH9mchQK191VMEynmz
IpK4USWKf2qRm7Kb2teeQAx5onUr6c88yStK/1BugCf9nRyAzAegm8oNFTJwFDv63Pdk0ByQWWqy
NCBuGj6grC8ga6hpP5dqSLZ/eWqrs/yBAi0AZobmmZcBLUD4foC08IuHLxOTCL0OodnZGpI0ZVxm
JoGU7F7zQjKWGaW1cKJNaT9J2PxEk6BNpAfHZgD9efD4cdHs6xOn6DXqDVCAROYuHkug++np6b3P
Pffc39H3J/XLMRH1RzEKQDaLpEXoHRsbu/2mm276fbKJavPz82QyTYuTJ0+KY8eOiSPERY+Ck9Lr
biThGDUL3XqReeV3+pE8nu6DMFfTz3MEPPvTITLu8VaZh18Uef/95BiPQSgvju3El4ULdK1zOQCC
x7sZI9Jau00ynGQZ5YbReGg0AHaduy4hnBRn5TY/0V7oUzsRAj8XgGXuMT+NuxY2YUh5fgDtJD3l
wrvCi8IIPztSrOiH0bljBeiHN5HRrkMQNAnaBI2CVuEHqBHtRkTDRw8fjuka9A06B72D7kH/wAHw
IF+JWW/nmwEA/GTzd9fr9WvJ7v9jUsWGIPVnZmbE5OSkOHXqlDhBEh/7NHHPAXq/ZNQmLGr3mjWi
Z+vWrHddK9Gm82AXOYIQubRSToxFzT4yZ50ONBMRjtrLQaU96e977rVys+Vyf9OZVqCZ9E9bhOUS
dCRThnT71cCOBiUd00LbSsYmu4b0fJSb9MN9GbzAyatlELwSUrnMSvuhOb+sWmuvx4AINg3xmb7O
5RaIXHhX5xq4hNUnq42CNkGjNjoF2h2emxPThqZB36Bz0DvoHvQPHAAPwAXwcbFrAGR2ly+76667
fq+7u3srFmF2dlZMTU3FC4N9YmLiGL2ekjMzaoRUp1TVh91GtlyNFjhtBCmlMwDDB6FuJf39kltO
cIFmH7zDjXaO5TaUaE/6u1mAWufLfTXP9FM6aGpw6a/T+H+yx+3AhcoaXoj2gwCZ0pAkFCnlagGO
fNThc0uBnQpc5flKlJsNKHTbWgBnzmltgBBeB6V8/YH2GIHf9zGkBeiQFqDZu4wWQZugUdupGFrA
GrR8n54+Dbq2NA56B92D/oED4AG4EMm8lYuTARB3K9PFbrzjjjt+Z2ho6NVLS0tiDtyRVCIsCHZ6
vp8W5qO0MD+1o9n8PzctLS3y8F/3xo1JxpV02zgXOrD9whFfmocYR0D6W6mkQ7a/CrQTCyQKaZXv
5COUDkv/NC9A5XoSppKWSX9tOgtp83et2vAp+WnJK3081TyyPgRcC+Dn6xRD6XzNglMclPOLuFpA
4brm1l45acJaBVqHhTotCRHQGrSX/xBmnpL5n+JiIKJN0Cho1TKGyxqN0zc3m79LdP3roG9G6zH9
AwfAA3ABfAAnFx0DoIuKPf433HDDL2zYsOFfLS8vSx/8pBbNkG30a7Tw/9wv5VN31mrHuhcWqkl+
SRQ7WbqRc83TfotuqHPHiqW/9ttvBVp96SDxiYCq6DXkYGquDjj5Mu2koNmHVVeVDtrgjk/AOhgD
DkM3/h9ODHJf61yWocOYrDQWns0f8EFolW8JlrtWK2X9rkn+uinPtAj5bDxmofXKrcMc7cvXAkQL
XwD/fZYeDBqNndRRMui1MjfXd3tPT6Nb6wdA36BznwkAD8AF8AGcAC8XDQOAXQOP/44dO1KPPy76
9OnTKfiJOzZocT5Jqua3K5XKwuZSqbcvirZZ+1+Y+H/3hg1J+E+4nX4DeSy5HoB56a/DdmaahBO2
/XPhPj9NNWB2cADoAEB1oNmHdmrmVQZ2PwIQAErGWFqH/9r6m1XfTUg0X4/gFu5khVKq4FrCWoAO
dF8ucsr5fQV1bmpS4F6n11F038O+gLTYKKQFsIxPaZKVQKPxvEnjBwDA6qXS9u30guj7YdA56N3S
PnAAPAAXwAdwArycL39A9HKDP+TxhxOESX5NC/C3jUbjbwn889VqtXdNtbqlq1S6ImKtv6qjo6IG
+8oJ+3n2v+/l5uOyctJfhyUtI47sWIEUW0/6Y/hno9GMVboFsvswAhzhzHhoqFYBhhGWiDrkWOQh
QM7gvEy7sPTnn2/TCai53yCsBTjORXZeQbNIhwCuc+aCvzZYO6wh1jJeU1pbrLFSOujYCzUNce+l
CGomOpBfoQPMR+dqOYQbCaANNApatQ1qwASqUbR9Q7W6gaT7Augc9A66ZxgIRgbOBxMov5zgh2eT
ttTjD05nnX6M+32fVKA/oMU5ReCn664NDjYal3U1m5utjYVGjGnXH48BBEVYiCFoL+GkMOQXjhTk
QGukHDrPzMzNimNT07TTddH1LTcb8az6oe5usa5ejx/r5VJSGqYDzTOUKzHTXHrdorhIhSIFKi3K
0UrnihJXnQuYCk6TZKNLSS2AbbhpegokvQJVqkDF+QBppmSSuSdLvHVYklas0yINt61Yk9ZvdrEp
JggUR2g98bikmqJSKosBWs81pGKvGegXvT31eCKxzQNIE4A0ywpkqb9ZoySdbyDKCoWkYJ+XfqPR
gqwp6wsw3YJAs83Fxfjj1WZza1+ptLVaKh2kl6dA70T3r4qi6FokJdkdcxgJM3Fk4J/+6Z/eQ6+f
IBzN33ffffqCYwCtPP4M/CcWFxd/my70IIG/G1yPPjvWu7BwWdfU1Ho7Zivq6Um9/3zqjlhJ+vPU
Wqbq5aS/TekVwrMTdSCXP2MGp+fmxe5Dh8XjL74oXjxxnGy5Ri5LsLtcFleMjYob168T24aGRI/N
PFPazRAMmhWeSaDznminCk/rvKOywIO1ciZg3i9hs+BihiANQxBZGy7ecDWuG5B5M8y/XmmBHyVp
xnMk6V+cmBCPHz4injt+Qsxj/Lp0h49WKmWxbXRM3Lhtm9ixYb3oQ0MOC3rpaQEyYl2GebafShqT
su7BKfCFdDMcGZNIEqb8911fAGgVNCuRFowkoYWFDT3V6mXEAJ6hT04SFg4auv8zAv4oZwDYbWTg
a1/72ofo8+gyvHRBmQArefyN82OBFmEX3dznUSRB2zBxv7XEBdaBW0ZLSz1WA+jq7xe1sbEs5hqw
/51kmFybLeF23PUYhPQTUQLJM9prVXVsclJ89amnxN9852Hx7NEjYrnhV9QlX54ngv7eoUPirx9/
UnzjhRfFKVoHp6TYxtGVK/3DJoHK5wQo5TrnuA1dYNjr1dj/wvNhKK9lVy72r4Iqf1rRaOx/Z66A
CThibbBGWCus2bxp0uEbL1hrrDnWHvcA98JZB12U1JQv5PITfFwTR4e1yoJoiqVN0Cpo1jKH8sJC
T1+lcllPrbYBdA56B92D/oEDDxfnNTIQvQzgX9HjT5qAIpvnz+hGwOlXpkUZowtdTxrA+nqptLE3
itZFLAEI475j+z+X+suke86GY95x4Yd7Al5g1vZKs6wyv4YAr49OT4l/evpp8e3nnyehpQMZbyLX
WoqMP/HPzz0vHty7V0ygT53XXCPrBuQ31sgI0u2DJ5xWWzlPvFJeDHzlsiD/tJ0W36HfEO65uOEz
r3UYvzbhNjHB8bEmWBusEdZK5Nq4i1yGJNYe9wD3AvfEj+Nr5pzVWnvt0gJRIC8CkEY7QhOhfAc0
o03QasVkBFqm0Fcuj/d3dW0iOgcTGAPdg/6BA+DhlYoMROcY/O14/OHweJD+9kUMZqDPj9KirKV9
DS3MaI+UY3Wth3mhRWV4WJRt/n9LiaWDST96hSIa7SeFBMNMCTOYJVPmO8/tEY/vfSnfOmdFGavF
Q/v2iSePHIlVW8dB1tT53oG5qUHcq64yZmVtfhYtyBJ5hNcuq538AO18V2vhePct49JOJ2I3ahGe
FCS8a012rAXWBGtTzKZ0gYki4nuBe4J74/tpcvff7/QTCiEXpGv77ctCZwYaBa2CZjWrWO0luu4t
lTaQkFsDegfdg/6BA+AhYB6fl8hAdC7B34bHH+Df32g0Pg2PKF3UCBYDi0L7CL3u61Gqv3t5ud+q
/6ROJPP+UA1mM69EPr0zH97xs7wCmWChNl6h+XQ6SyZ54dhR8Qypp5wA0zFjBdKfFxIhq+6pw4fF
oampwJgs20JL51p9+Z547TfazEl/JVp6AdtJBHKkuasF8P6EOqex6FzrMO01MuWMDWvxlJm4myu6
CmgBWmhXS6Ed9wT3ht+r8FxGHZ5D6ER/RC5bNB829NLGGW3GWivRLGjXvldvNgf7pBxG7wvGBEZM
ZODTwEUAKy97ZCA6V+AP5fgHuNoMqTa/T3+fJhVomCQ+wD8Gzz8tBgYrVmrLy9jrNoSClktVE1fl
I6KdkVKBvPtQBWAWBlKBEFI+RdcPSy2Qbfb84SPiGKmbmSZaIJlavHeA1Ly9E1PxuCrN7ePUCZlX
n8MzAbWTj+/UAYhiP0Di58zeVKEQYbBNEs9G1IHqQxUM/2VMyVWv8TesAdYCa7KaNXSSvekf3BPc
G9yjXGjRSzkWgdqPzDwRgUzOcH2CZtEBZzQ8moQQzYJ2pUkJ7mk0ekm49RHdw9k9CLoH/QMHwANw
AXz42vLLXTNwrjSAlh5/UwHVWFpa+hwtyEH6bL+x+0doIfqMUyRCh5T68nK5trDQaxez3N0tukid
ys349TvJ+mDXotj2D9l8oTx7z6SYIK58LCXUVra/CEp/TlhHZ06L04uLOenvdxXSzEmYK0BS4Sy8
uDRYiazqLpDnt3IiEKtTwLGaqvVvMomuHcem8rIIXS0Aa4C1EMEqyLzdH/IF2HPFvcE9yvsBdMHw
1zboQrQoFAo5As0OmgXtWg2ge36+l5gA6LwEegfdg/6BA+ABuAA+gBPPX/ay1gxE50D6t+Px14uL
i/fTx58gblaHrU8LMESPdbRLipIptovoBNS3tKSjpaXulAHU6/H8Px2K/4fGdgekvyPRC6R/auMW
SP+YWOlGzMWgDSTV6pUkl+tBBuHP0Vql9jQ/d+Wr0sIdF6ZY6zCl01oAN8lG5TXeImEaaqHgJMap
fEgwnm2o84NMFVPZVSjfPzsm/o41iBlhjk3plna/kxlonuLe4B4FE4x40lKBFiCUCkQEAsNVg2PI
Mw0A74BmQbv2dbSwUCXhVqLfWQK9dyWhr7rBAUKBdeADOAFezldk4GwPYj3+72/h8UeTjz1ky3yF
LhLcr5cuuIcuvELPJX0frVIWms3mbHNpaaEfc9a0LtmWX1jE2AfAHYAsBZPfQJkbxW3zTPzwj3Y6
u+Sz7lTw8w1Ml1Vev34/7Tc3iz5rtsFt5SW6zmbDz3VvBvIPlNc63NrTWb4CrwTUoUnEugWminiV
ds83bWYqDZhL0plQjMWUtmmIMj0wIzNDUKssto5hpjJJm8VrrMGSMYXSnAQ73JWzBTv9N32us8Qc
8/u4N7hH6b2VjC6cYaXmuOb7XJXP6Cj5Ic3+tXMI7Tnacwg0uY1p1jKA2JRVqtTfaGi1vDxTSnoE
VumhRLjoJtov016h48zT41cIL1uJSWwHo/ByBGxk4LlHHnnkj4gJHBdp04fzzwBsV5+3XXnllf9T
kcef1JdJ+ttf0ck3yd7pN9l+ZXquaRGWcdG0n6bPTMnFxUZfsxnxkEq5vz9ZyCJnlWOTCbcVmFNy
W5Q+qr0sMJHz/luGUpZJezLRtvT3Emq4zYQbappYOnnmvEeACtikTkagOyMgFxYs8F4XnaUsyqWw
51Jy6w2SPBqZNu+0GYDZBZn+fdJ0MhYynVhs25zhK5Uoymt2fmPOnD9CCrd5XzKUo2wTf7R0uwWx
mRFSy7Q7kc64jmvbp92CUqdT1mcxbURarJWCZsssFwBJbf04mcXF6WapVKZ160WjUMIBmuJWgR9i
BmACDeCFcPPLhJlBP1OwXq+XgDfTTejvSTOYFGfW9PGsGEDs8R8dHb0DHko66aDHny4CTT6/QBd7
mi62ZtSeEl0zrUEJ2U1z9N0p2ifo4qfI9i/3at3F+65jIVFmGUoB5hLa9cqvUO6r8vFiqfNxeD+E
1F+riR4zKXgl6Z92zQ00JI1nE2C4SbnEwnhNp2+AW/qr3CrCUDlrIIEoYyAi7y8JOv11PiNQ6bSf
n+BpvYH1jcFlW4KlY79tJ+Cszj/LsI3iNeiza2oPmTp40z6+FoMttAAd3xvcI94nwILVH1methe3
30+nDUt3be14cE8L4BqDQ5fmOWg2FlzMeU3CrVxZXJxYrNU0gRn0P0A46CE8ABcV9MUkHKAp7mng
hvDzPvpcVyBdOI4MEM6OnDhx4kH63MyZMoEz8gEQF6r19/dfc+edd36aTmo45PEnhqDpQu43Tj+o
+zWAn/YmvZ6n7wH4J+iCj9KFH6PPHu+jA3Vr3ctDgCVmR4XKf1tlfOUSg7zCDicJKNQWTClHAoK4
xvr6PKnsawPaVQz81lVmW4v6gErFAIxP0fKkv+OUVGmZrA71BmTede34NdrvDez6ANwxaDybj2ci
ala+qwO2t9PLkPvh6H2sAdYiUJHkxlj8++scKHkf9yZmAFwDUvm27Nprw65XoJVWGaIhAWP9VaBd
HgrslbKne25uhsB9HHQP+gcOgAfgAvgAToAX4Ab4AY4KIgPDwB9wCDyeTyegJMAO33HHHR/v7u6+
rAD8cFo8Qxf4JLgWOBzsfbrAZXo9Q/sELp72o3YhYAKMLS3pEjEAe4vRBLTc25ulWYbSgP1Gn750
Zk6/lFCdKtBw1Zr2Qkb4r1Ypi8vHxhgTEHnp7ziQvA+ZY23q7RNb+vtExRahGOmvCxpp5KrxhMjU
cCdJx08fPgdeIi2Cx3Y6DSnlgkd5uQ1OerDVaprxwbEGWAusSS5hi9de+DP+vGvDPcG9wT3SXmGX
DkYDtDMc1o5i0wVOQe5XCoYJmQZg/VWgXdCwPV3Sc3qHl5YU0fpJQ/eWCUwAF8AHcAK8ADfAD3AE
PIWYAPAHHAKP4gxnwZ+RCQC7hbjOVcShBD85OP+M0w8c7n66iEXiZuBqDbq4JfraLL2ehspPh4l3
ej5Nn52l76heUpFIxelPR4BbBuA7aVhRkPZUNj/eK0WRE1CxttZeeqfm7bjdkNu20RGxY+1acXxq
Kij9dQD03BEIO/UaItT1JB1Sj75na/MUVBmoQ0jPr+lK/5zkEzqo9hflLcqgOZDXhISt7Itsh+Ao
qw60PgF02mVrnmoPzJFmzxtrgTU5NDuTFPFyB6DMzsxR27kvgJ7jnuDepOeYzg1wW5bHBWZaM1Xe
0IKI8k7AVMUP+AL4PAqek8KKg0C7oGFpugORkd832GwCvDCJF+hTKCCBH2yJXjdg/yMyQHjoor1M
+yKB+37Cxhhm5FqnIDIIseM5cAg8giGczzDg5Le+9a1/T6A/aR1/Nn2ROFbsyaSTnaaTVAR+cLUF
ej5F751EuJZ2cD48nqILQ1LQHH1/iez/bjKCEvEKJ1m1Go9eFsZJpL3JMTqXmpm3TXWg1ZczB9Ab
XOn27VNORyA8r5Ntd/u2reKGzeMexnXANPDCVfT+HRs2iOvGRkQtLm32mmnw32XvaeVOIhZOyy/X
Mah5110P0E4PwUAehfYTqpzvK+avUHlJzZiEc848v0EEpiZBs6K1wJpgbXSogtFT9d1MQBHfC9wT
3Bud6wiknGzF3Ag25gDWLTo9uc5ekTcX/IgA/FdEu6BhYbJYS41GvafZrGHqFege9G9wcBS4AD6A
E+AFuAF+gCPgCbjysQb8AYfA43l1ApLqsUgc51gz4WaQ+vSw0EUnqci++UeU99LJL+Ei0OSDdnC8
SXofgIfkBzM4TQuxYJwhSBLqqkVRL9kX/elgQOtIsVyWFwNxZuBYBTqbHVfECJSbTitDY7tZCDGd
5Wf+Nkac/e4rrhBdMhKPvvSSaDb1itK/GpXEneMbxS1r14lBqKmKd8IRmQRn6jTTTbPpPyKT/tIp
JMqcn9pM8En9AWem+afXHmsaJVMKnIZPMy1AWS1AMG+/NCFAfo9MeFCXMsYrjWNzkO71nZs2xVN9
v7n/oFg0vQZCWoAN4aHf/y1btog7t18e3xO/5ZqMsnmCzugxe21MC0jKhXVQC7DEoI3G4fii/QI1
RqfcgR23ByPa7o2iHnQEGhwcbCi4/SsVPDYIF8vAAiJjeE3Y6kOIEPMCCFMHgSvCyNsIZxF9f6m3
txe+AuDvGPAIpnBeGMDNN98sn3vuub4dO3a8AWmM4EynTp36CzIFEMtHf/O9dGKLuDDDySDhp0hd
OWU4FTjfLMJ/9N7ywMBAE91RYEpUeohlLi/32kUsY3qLabDoqKYBp2A6zcXXAHLZXTqX+ZeT/k4i
iRJ8mq39zTVks75pxw6xdXBQPLZ/n9h78lRSEuw5AbvLJbF9cEhcv3ZMbMVcAzuDTruDQQUDN/f8
a6ctmCv9NdcW/JTgFfL+2poMJIRn3qDOP4pHgpkRfO43cQ1xvwPWCETaISAy9cCneQJxyM4wCno9
2FURr9m4UWwge/7Jo8fF85MTYh55IVz6ImxYKoutI8PipvHNYjup/n3WiZiq+bx1WBYO5DkBOorc
mv+0KUg2+1BYc8HxgImsBwIzQ6VvaplGtqDhlCksLdW7arU6YUYTA1gmCa7oO03DH2JzANExwssS
1H9MyEItAHBKDOAxwtcpAv8M3hsaGnoP8Dc+Pv6G3bt3P0G4XPzud7+rX24GICcmJsq1Wm1806ZN
70K7psnJyf9OJ/TPdOK0JrqXHgn/ZQ2bn8A/Y8AP6Q/wzxB4Z+k5bBtwPEUqTHzSY2NjUWlurptu
Ts12/kEudaoBCOGqWbnGGG4jjphJhDzAyvoG8vH5wo5AXjPKWPrS2/3VLnHdhvVi29CgOEEc+OjU
tJieXxDLzWW0gRIDXVWxtqdbDJMa2IMwDr5lMuiCswe4fW8BFYPO81U4tr/rIc+YmQrmTqxUaxdM
t7Yef2mkHzdxfF8Aa76pzdSgeK6jE4orCb9br4zDi1LUyxVx1fCw2DwwIE4hTXhuXkwtLcYaQaVU
Ef3dNbF2oF+MEpMA8CEF41OMtZTI9dmkeQks7m99SCk98XUTidbAzUxT3JPmAPAZgkX9KCy4oAHU
aqkTm7TbalnKWl9fnwTdX3PNNbEWQPhQRgvAvmSYwAL95kISPJDIlsVJH4KzkD6rCXcDa9as+Rng
8KWXXvoi4RL4Wl5tOLC8WulPP9ZPXOe1pHZsPnLkyB7iYujld4JOskonB5Ue2YFQbaAFgAFMQ92n
v50GV8MObgfwf//731dpHpfWslIu99g8Z2k4qF1AnwnkQZv3XMefUyo3LlsERl77fgXbjoszCt9u
ljpx6g3SOfZjBl3/QBzPh2kU0d8jjKWyErnp5fkXSX8nvCcc6e/a3nnprxRrCY4+hYL3y19dGNCu
qeKSjY6duMuiWMV3tQCmSRktIB1Mksb+JcsXcLUA6zTE8xK9h9yAPmKc4wODQkVJQU0pHhBbEhFp
VZHpuefca54RyrQAycwAyUesB7SAdOqwvR8c/NJLQBPFDWqsACuZgiCzSgiH1bXxTBL9gwngvkHt
J54ikR8Ap2AD+KHPwFdAVkNUJWGLHAFlzIRF4I60gRvXrVt32caNG1+7f//+lwifp1arBUSrAH8E
6U8nsGHbtm3vhyODmMEfkqQ/AO8+XdgUMYUTtB+h/RC9PkTvH6GbhuF+mH02iwuC6uOBX9x7771R
pdEolbXu0cyzCg+qtaEc7z9fbG7TKTckqA3hhdJ9tdDh8mCvbZhWAc976nBzW2WVkQKKSjB4amVk
R9XnS2i1G15MwR1qWa288mblOtlc557OJzq1kQC0YrKQ1yaNOwtdh59Xb6/CrddtKFb7rbv90maR
CHGsJdYUa1uOJa/wpgIZJtr027F76dCioPxXBKouLTNMw8aBVucBWpTMERjPsECuhzUR0N1KiHq1
2Yx27doVfxk4AB6AC+DD4GQSuAF+gCPgyeDqBHAGvAF3wB9wCDwCl8AncHrONQBz0Ihsl15SO66r
1+uv2rNnzxeIKz1O3AhZSODOTTqJBux68xw2DFQahAKXPJU/R41renrK5fn5tA2YLQVGIkWcE8A9
rLw3oNOSSeRvkGUCvGYgkEwkc3Fi5VXFFZgLubhyQTmsFwuX/qhvywyM9JdOY5AC6c+Bkx5H5Kvu
iqR8K/Wf51Eo43A0TUGTrnhR2vMv/hubEBx/3tMCLDOWJdZQ1Dr3JLfXLeNLji/9tZSBnomxcPA8
82moULrnwbQAhw5YiNlR93kEKnYsyrw2yoWQ0QpUUiiTlgRbJlCtVOprq9Xy008/nR7oqaeeiheQ
tAFtHIPIFYCWvERAh8pfRTgd9QIIDwJuMH2Av4MHD/7d5Zdffi9wSWbBAfjYCK+CNAF1TjWAxcVF
GCprtm/f/q7Tp08/c+DAgb+kkztJJwln3gw4E72eoJOfpH0Caj+9B9fkPNk8sGvUDTfcoN73vvd5
LdW03LlzpyQdBxZkNfXjIQyIJApms0leAKSzOD9/L/XlpGOyZa5nfFayqr3mIl4psNJOg45QJ95Q
G+zcaDAdbuihee85LwLAz9HvH7jSNKLcAFCtW9r/QcbghVd1q+lHoXNz2nApNxLgRC5UsKGI3wPB
L3IKDRLhXZI0mz2odT4xKB3v5Z8jX2/JGFLKU8J057yXFjTpmIZtGFAkeSC18vJyGTRvTIF0kYEP
4AR4AW6AH+AIeAKugC/gDHgD7oA/4BB4BC6BT+D0nJoAVvrPzc3Venp6NpIacvWzzz77H+nH99FF
ztEen6g5KZgCswj94X0D/MZDDz2kbrzxRmWTF/zt0KFDsrerC/2RynbxIPHLZANaO82ZCGSjAEyN
k0IG49vcDNCBzr45MBc1EFU6EOLTLQeGhLrmCF466zQn4dEIwfwESRchNy3X6xLE1WqereenARd1
AfKe59KBeSqyleZeybLbjkyz7j4qU8G9a9U80uFPNhI631MwOAAkkD2oWjT69KcPefX/Oqf+60AV
qnQbg3Ct1GYCgiZhshANRyw7UJKA769WS6D5nDpO+ABOgBfgBvgBjoAn4Ar4MsL2NN4H/oBD4BG4
BD6BU+C1XVOgXQ0gIluj7+qrr37HsWPH/nJ+fv4J+mHE8mOgw1tpQL+Ik7bq/je/+c0Y+O9///s1
b3sciCzIeqVSqpRKVa7ix/YTy8jSurgpg6PG2li1domaVwhqp8mECgBYOOOp/Im9qeRQjOBZrb7b
HssP0fEBoJmmkZkWgf56fmtwp39BoHuQUoUVlK1HgwWiACowiUdkYHdzHsLnniVVMX9HGgng669y
FZGadyGyzk5v/XOTiLVvFvlagHLHmgvXx8GTf6RTZeo3Sw7VbGROSesDsK+7yuVatw1deFaXzfQD
XoAb4Ac4Ap4MM4BjPcYbcGe0gCngEbgEPoHT1Wj20UrSf2hoCDX+SEvEeVefe+65/4c4zTFzEsjw
i4GPbj7gWg8++GAM+ptuuikGPq7VAj9iXVKt+p++aDTKxCmr0thK4J6woWSgTDVUGKT58A+Zr2UX
wWSfrLY/a7zBxnClUTB3vp4OTA12pY3r5HMjDpy4lWt6OCor7w3oNeRQbLS28qStChSmnHkZQCCE
mmklKcNzxnyzqj/tXosDbOHlXyhfzQ84Cb2aAJ1r4sr+xkKkmmcF5gaHqhb0wUOHLNFKFBQAsfcs
3cY0bMbZxbkBRONRs1mC0PMxwHEC3AA/wBHwBFwBX8CZ8asBd3GoEHgELoFP4BR4BW7b0QLacgIS
VymTfXLV/v37/5Q4zhHkMZuQBJIXmgMDAw0k8+BE4YCQbGIqfy78sInZ1q1bJ/crZJjotNWRRsjH
xnitjWVDMsH4q3Bq/3kZqU3ccKYEseo7qQNS1Mbg/aGfvFpPqZz9GezdHxiJlc3689JTRd4s0Zr3
DeCZjmHbXwfamrVTDZjrd+8dQ0peOu1V5QmvJbgouQ48rLN1AOosDKhLWdjVSd9FWDAOKeKlNL+N
9ZRxcFLbEEEaTrSlxlidyGQBmgEgSqQNSHTWnSVZ58gON8lSxCVL7jHZ/16PAOlUJftVgNx0AA1r
Y/bG6cBCVCQxANB8ThX2ogj8+S/8wi/AQagff/xxMTw8vDw7O5sYVUrB4b4MXAKfwOnu3buRWrx4
zkwAOpEmMYHnJycn99RqtRl49RuNBuz75d7e3hj84FRczbfS3t9FLq9KILdZ1splYo6ynALWmAAt
1S2nR4BnkwUKgZxyUK91VaIMBGxCz560o7KyajhdDBqepOO00Nb5wZ9aB1Vt3vzDifcb5qWY7Z9r
JBpS5wsyAVt91vdpWF+ASkuAmUbAR4QrFTRNtA4NEM1PAM4PZtEB56S5L0q7TVq1qwXw/Iskcui1
WhPhGgDpaVKOpsEzUgvM0rQYyGoFUVTpqVQi0LxvBoTwwvEEfAFnwBtwB/wBh8AjcAl8AqfA6zkx
ARBKIFUF9vvSgQMHXqjX63D6oafZMqkY9FvLTQv+EOj56xU3pcAmS5qV/sYZgb6DijsDczQrs9bR
aZgw347L7d7Jk2oCffi1W8CilVeVZ0HQVHmbNy2FVQEPdKB9F3c8efFr7c8LEC2GjCoVTpBqkSCs
i5MCvNLYwFDP3Agxkc+n4A5ZL2KifTVeZ70GeaJTyjCbbphTq3x3JK0L7qXSbEqwq0VpHZ4cpNNo
AKMx4dUDmIo/n175kFCVfLZsaL2VwM3hhzMDywSAP+AQeAQugU/gFHgFbtsJBbZlAtCBoeYr63zB
wRcXF+P45WoSTOz22c9+1nlN6oyMyAQoS1lhHhFh+wKmudeWIXDbNjTdVYh8O7CC2L2fmGOTaGKN
j7XeliI/bsyvutPBJiXCbY3tOK5UnsHkHFgqzZDLJDzzqDMpprwogmsVr9IEcArx2G/G/e1YWa9V
56MSm/Wn4n5hcS6iyrzkmerPUmlNFiDOPyn1Nf0DpevI9e3x7FYk+QlZHr9w6gDiexjxrj/aTReW
gbyNNCeA2fu8FRwfNMvp09CtaDTSa45pmDm+K0TjdF9R0JOTip/5zGdWA6N4Ia+//nocHIxAQvKD
QUxNTbUNyhUZgOUixHUiq4p973vfO6tGhJ7zI36slMsR10ikz1FtaIVXaHmJQZk9L1fs5pqaCTx5
yPGg5yMC2Ry8rPRW2gw009BTM+kvddbo048AODkBipkryutVJ3Q6DtspUCoct13g9GyR7RdsBVbU
KttJxlFxW69M+mfFPbx1WAoQxXLvGfikrSew9y0tJmqa+2Mzhk3SkGqmhIOiHqkV+4wVICUvpKhc
P0DsUwo0mM11mJLOY3z5rM2X8HoD6FzFofQd3xGa4zYy2kfBH8B7Rv5ai0Wy/SOrKTz22GPqnDEA
uxUd9IMf/GBLB18rTcc+AffS1WpZzKBWSKYmQGScgH43IF3gqU6cJiwBiDXFEKn65nZ6UYZpOH0B
eSzZAp3XjvAJw7rAVuYYdNpj23bdyk10aSonT96x/Z2YuFtz79vQThKUCvsCCpuC+v3tPF8FpgHH
9QBSplN9LaglL8TiDUSFAWfs2JVZXURJuJl/cBo6Dr2k87Bm6y21X9Ir3A7PXgdm28dQGC1Aepmf
8b03WqU2DEKKbAS4ZvUAGY1FLrhDFZXWmWeiAILRNP5ar1ZLPUTzHhb0hz70obbTtH3N+4knnjgj
oXzWvcXbtvELtvvvv1/Oz8/LMqlFpo9LZnMtL7s2Y0EKMAcfUjUTe1zkuv9ooYNA4NmAuVHdSnhS
360BsO2tYomfm5zbZGO63Bx5xybloSs+9ltwx6AKTN9xw26ihd0v2igI0sJttR48hq1atGAWWQpv
XgtIPpeV3etMMzBagJSMiUUijXDYgSQZnZnjKpl49i3+ZZQWbjF3jokelDItIzTKK8j4WCGYjpiQ
16x4KMAofdq0JhgmHFs/gmFvDdIClojmzxRv53I7JwzgTH53x44dvWSrYEgIqp0Gtyh11dVSDneL
UE53wE7lZcHpa1Num0XlMw6tA9NejR0tc444d8Yel/y5rEGhc1mJTtag7wMQLP3VMoemFz9nwzad
nv9+RMH8LUtO4tJfJSO/vG4/bUkYpsKquKpRmXTWRAuQNqxn2nxrx5ZmmkPJ2uAJmGWSC+toAUkZ
gTR+lqzWIPUBiCwao62mwfv1h+5JqglYJmLCdyWZrwFhvQHS1mVRRjlsWoFhaGWnnJir+DoPjpwz
dq7Z7N/TaGx/8YEHFrdu3Yr03hmy4+foT0uvBCN42eaOt3AAluv1+roNGza8+6qrrrqLFmBTuVxe
X1pYqC/t3t0j4l57RZNbRW4eO3cGSqY9SCFyAx2lV4OuOUDTDELuFXYLYnJNQ/j7TeVIZ9vmW+pw
4oszJccb8a2dbDWvdNj3bItAiMxv66Vbz9zRIbssWGIr3XURmZqftv5Wymn0kUhr6fZjtCaC8Aa3
pGo4rwEw5xWVsrVo8vOWsRaQy4A0/gEb13f6PjJtJtUAbMRI6lwBmKPae2tTWA4c6kQFh/fQ0M0b
t2379Gilgq6/+0kIfuOhhx76K2TEi6QpyHndyucZ/Bgm0nfddde994orrvhks9mUsMPQXDSe6sJ7
3UGCLS05TX5EICswJUqbsiqEm77r9ATQqUNHe84+N+FHp6q+ZENHpBe+kv7MPe0DWXhJQ25YTVvp
b/sB+IlGLA03V5LqSf8sDVe5NQ3thvtEQWcgnn4cS0uR+AICWkAMHsmaqcYSs5R639NeBSXJEoFs
9zCZJRjZv9ljsbWNu/04pfnaNSWEzpl/SXDBaAERM/dE1h1ICpmfLBy5jCVORDPX5DijWT4KZ7Bx
yhKGlZrrxmui8zIdZ5SEIMaDX79mzZq3NxqN0vHjx/8T4WPyvvvu0+cTk9F5Zjilnp6ecVJ9PkwX
LRFKxAAR9DNDR2GMiMoV+jCmkIYNGFeWXhsmYdKInUQgwRPX3FbP3CzQRem8XoNOnuOv0jp05VUb
co1BOW2181KUMa+0oMYr6mGFMzroD8iuMysean8qWEhD4AVBqrC3gnKqF3mRjZMKzBK1sknB7lq4
rce9PIuA01TxykyVb0QaSiN2GqQoP0KkvNGDGQ1JG8pjEl/ytF8eTUh5p8oVDKGz0czsbEz3oH/g
YHx8/N8MDAxsThIFL2INAHMBt23bdg/Uflw8WohjRz/AJj3O2dbGtvgHPfY873+q5nNVzKr8gudr
Z5OjtFev77bNcr3pkhfz5LrHet9vIf3z03qEW7TCpue6rb7y0j/X316IfHdbp1uvCHYGzsX2Pc+y
LPQLmLbZqZouktg7T+tlORpObN3XAtBOrRRlGg9kr+0ulHbk8UwFngtg/Q3SSSJjGgRr4+0PeLVa
gIkyJGFKk6sgo8BkJ+EJjyRsLD2Bo1mUSvs+gEYj6y8IHwDR+qnJSdFF54zOUWiDCTxs3rz5HjIH
XhJn0eH3R1oDIPUmIgaw/vLLL4f0j+wQ0YmJCXHy5Elxih7niSlIxj0VpsZysPvdWjxbN4tI2BCf
aeLAOTfrKqsD46G1DmsA2u8TYAHbyEt/1eRVg8oZ9KHtJCBel5BKVzjdVJrt5swJ8BqLFMX8NW8L
xu3S1SRsBb4TPG6gbt8ZUsrGlcfrkjZYFVmVnsg6I2ep0t7aKbOmfgSkYTMwtVP3r3OlvjrsF7Ha
R9pEwrP1bQ6G9SHlY/pu12X/fiD7j2hYMxNghoTcJDEA7KB/CD/g4bLLLvs3wAdwclEyAHj7icu9
uru7+3Ir/dkUYbQ1PrK4vDxvVav4BiIMyKfGGm7rRAKkzFRVrqZCskQyPxVGsHHVwlUb/R7yOpee
6iXfOAM9tWte8GM7TTuVM/FXsJ6B2ukozFqG8eq6FtLfn2xj10W1OR6Mf8b5jj9ZKT1vz6chBHse
GrmetSzPGIZyx4xzBx0fR8bU9JS58ISd3EgyrxjKScJS+VFnKt8QRmvbAYjZ9/Y6A5I/7Q7MGQRo
2OSagHksLC/PTU5PL4EBwPQ1g3TQav9y4AM4uegYAJx/lUplbMeOHf8WTVBxwdAAYAcZE+A79XL5
dzZL+VXOoZVhAMHkB6u28i6vUrIhLtoZHimdiVJes49Qn7uCLj5C+VImI0hbn+7H/1UKUJ1v9Jmr
UQ9L/7TZR9C+FnliX6EWoK1+ALnkJq/RSMBPoVnVoq8FZCDnxxLujEbj2FTaZxJNtr6sCYlSOc3M
7y7k31enf2J29zPnXfpEptWX6fu80jWkKXn9BpXJA7DbpkrlIaL/J+yQD8sAgAvgAzgBXi4qBkDc
rWfNmjU39Pb2Xru0tBSrPbhwLAJdPIqL/u+1IyNPdpdKJ3iFXxNRANtLjoX4bIcg6TlrePmk5iq+
FCI3I44l48i0M68HJBVqFKLyPgXhFw958X8m/TW31bU/+YdBUrGClbRnoMg1LQlNNM7N6muV5rtS
unDgmO5vuueU+UO88/e0gFw9hGJJVtzrz7MquZNVBPw6WuUbf/AGLkyDkoG5i47GZ0uGNZ9WzOiO
OwB5G3GmBeA3QMPcX9BXLh/pKpc/D7oH/VsfGHABfAAnwMtFwwDAzWgb3blz50doAbvA7XDB2I0X
9Fm68B/oSqW5mAxJSDkxFq8JPwAnZNYSLBs24YZkFCYW0fdOz5GZQYsM30Kj2czURlPXHR8zkq4j
T+en7Gg/9ZYP7FCepDEqslLeKC2vyo/nGAiRhR1VU+Vs4jTE11ReEZPKSWbFqwoLvPqrigCwYykd
UKv9HoWprS5yPg9rx6dagJPApAOdl1QWgfA9+8q7B7y60DlP4Zph3Ga3JiLP7KPvg1ZAM6Ad0BBo
CTTl50fEyVHWJOXmgPkd0C5omK/7stbzBPAfEt0/B9BjspbFAvABnAAv50sLOB9RgOrQ0NBVAwMD
t1vpD85nuJ6ii/0vo6OjU0vNZt9ChHojRgjID6DvlLkU8gsxbEUW3SB8Z4aO/eKhg2L3/gPi2KlT
MRFhiAQmyGwdGRW9lbLbfCLtepsBU+ZmyOmsuCdYhKMC0jYb/OkwFyb9FfN4O/PvGFNwMhRFfshp
zvGkVHBk9UomQC4K4M1hdDz6/u+yDkyZ6zzzT8QykacPs0IblebsRyaJSLqONZY05CQl2U7Ett6A
pSPbiIIzg0BG6b1N6wBY4pFlLjPLi2LvyRPi+aNH42Ev+N6a4WGxY3yT2LZhI6R0/L24WU2oPTjT
lGLpb/1YZp8TYqna0zNZnp39PNH/7xIOYoe4iQYI4AR4offQ1GPhgmYA4GK1Wm3k2muv/SC97LHS
HxcMzkdc8Fi9Xn+YLr45OTlZny+XSzzm36TPYE+J3Uh7a3spY4dZTQDhlfsff1w88eyzYsksPIhr
H93M773wgrhmfFy84VWvEiOkYWklWPYX6+Ji1UshPPVfuNJHmHJhfxQ2YyhF0t9JrBGWGShvuq/b
Z0970h+Zhjow1txR11cK+LeTHcRCbSIZWZ3zDcj/n703i5HkPu8E/xGR91l3VVf1RbIPNu9jZEnW
AY3H8mIx2B3ZlgHbq4GN3YW93n3YFz3ti+UHL2BAz14YWMD74IeBLY8HO2sbGo8tWjJpmiJFimxe
fVcfdWdlVlbemRGx3y/i/0V+8c+oPsRuddusJKMjK4/IiH989/H7gvLrcd29r8t8uWBITunx9cQg
m/1pzfSy4UcGFYPeG+4rMF1BXYzlc8mxZUyHimb6WWqMwzgG7By7UOEp7JK2f+XDD9X5GzfCojQr
rDK8vr0d0M8LZ86or7z4opolgeALrH+b3S01vqYJ+tWPbjj0dkg0/0az2dwiPlhifgB/ZDKZAvil
VqudJ/5Ze9CFQQ/aBUiTRHtidnb2q6j2w0UK7Q8p/Je0ELv0eoGYsDJMpTKegADH4g3p8xN+rCVK
S7X279Diff/HP1ZvX7yoBu5oHInXAA7DkaveW72uXjn/vmr1usJHHjOndUAqSXbmxfD6ZMFODEE2
JHTPKM31I5PYE26AFysK4gGg/kSRT8JEZDO9JesAZExDpk3v5AIkfF5OG1Ix8NKE8uOE1uSoECgW
Uxlfu0Q69g0wE8/IBMTTsl4cKTkGI+4lpnAtz4RlD48LmgBtgEZAK6EcGcf0QVOgLdAYaM3XRWsT
LcDCUgHtSgEA2ibKA7x+nui+Tvu/klYx+AN8An4B3yg9JeufpQDQkf+pp5566n+wbbvCkX9xoYA5
/kuMESNLoELPq7AAXMfpsa+JHKpLZpgJCeUbFVkoI15dW1MXb93SAzpVYmHLkG7a5a0tdW1nxwBy
VCJFZ+bV47EAFSvDncyFe0b/f5Q2M+f7eeMipOC5y5FyFZsaHJthYEBwT0BcG4x/v7IAvhlXSIIu
O/A8VRxoxdXXylkRFQcKnRx0Ml5LXtuJGQzynkiLzTsICHacPmQaAE2ANoZuHE3LEosE2gKNgdZc
z4srJEMgYwPteqFvHwgyN5XqtcgCwORfDP8gbf+X4ANWjDooDtSfCvgG/POgYwEP0gJwKpXKyaWl
pV9k7c/BP63938LoI7gGtEDTjuNU+yQAPDKPopJWBAHb7Vhe2xwJjkefbsx1unntnukyWbHEH/7t
DvpqdXtHF6UoI32VlO7zRHmqTD15sSYdf0JoxP3v2KCPCVQfQ2t6npgaFK8DMDWuJwZcRKZ/EiT4
T1IIJJ+LY/O98BIsklgdgBe/lkRrxuiRiEqdjYIkycy+EUuR98SPlRR7ielBmT4M5YYX0ARoI5Yi
TuiOAI2B1kBzKiFmIusmQLueDgIGf2cyo7bjpMjaBbxWnnz+Tdr/iK0AbGwFgG/APw+6PNh+gNq/
evbs2a/Rfi4h+Ad44/9A7yHoN0VfgQAoD1IpNbTtAfv8LABkn3pSWyukMW6MO7pzMxWCPzDhXJku
VEarsBG4k76/kiX8Rn55rKG05nLdGNy1p6S2jiMCSaBPE+ormvXnGrBinBN3PUPYMNErEYWfHOxj
mgCThX3aVE+Y2ReiIMXPQ2lLJophGGXQEkBUzu3zhRXgqTh8emBqizX1dOxjMtIvgoZJFqPRAxD8
x+lmBOfCXPwd6Qc0FtCaNwkHJ8FofSEA+LWB4/RJySErVsXob6J5fOw/EMOP2AJgBQm+0fxTfZBW
wIOyAND0s3Ls2LFv0MVZ0sTBxZHJv0pmDiYL5Wk/Q25AlRaj1E+nXVqkXsQYdPMHrdZECWoMkkmF
QzmL+TwGpsXTMcKI474A27JVPpMJZw3GtJIVT2WZVXUSDkykqORkn4i4zKkxE4Cjfqy12GxAgmYd
ks/ZoevfJ4JvEtG1aBvIHn/PGLqpQVAYDMU337/XR0z7xo89xi9QMQsI54ZzxLninHHuuAZci3fA
cFaVmHHhYKxRcuvFZwLIwG0sdZh079zke433QAshTdhRCQBbkLLqNMD1JxoDraWkz8/Yf0bpdEC7
7thtIeYf9tLpQDkS7c+C/onur4MfwBeGi4wmoW+Ajx6kFfBAsgBo+nn88cd/jvYrLNXEhUHr/7/E
9BgcCs0/Rc/LgAQnH2k0wuQTkX9mC8AXlX8xEBAVzFxWxxcX1Y9zueA3ZDluTNXRPctn6bNzs3GA
DwElZkU33UCQ8ZXAj09IwYm5ABLkM3IllJ/Q0x+fXoOMBbrF6oOhutHrqrVeXzWIkRCRxsikWSKy
ZcdWR5yUKgP93pwAJCHHb+PX3/VwUGkEM2IPA2hwLICe4wz2R65aJ0ZfI0ar0eswplP0Ht1ctZzL
qmO5vJrOpFU2WGtnfN6yiSeKvMtsi/ycF84IwGu2ZQB56h4fbvWQ6VIVH+kVFpLZ4ywQbaCJD9bX
1KDbTV4ZTVNFojHQGmjOF2PAlGGhsgUgy9OHmUyP6Nsimi8i5gWjAJN+iSf+M23/O9GuxfySJyED
5gcfvf/++9fVA2oSSj0A898ulUpB04/ruraM/CPAQRdap4+dp0XApKHA96fFyNFzm2Rlp2dZLSn1
RyRFPSzk1FSEDOwb4B+YFX/8yBF16uhR1aTPh4FAfzzDjVMS9LknFhbUY/NzsfLfmKmo4b0mW0qF
luEUnDfZljsRfPMNc9efFAT8XoN8vw9abfVOa1/VhqMJpJsrGq5qGfjwJMgeI+bKSaRdYXEkMbp3
Bz+fP28nCQuN2xcJCi0IyFxTV+m8f9QfEPO72qy2uEROkWpTP6Z7P5tuqRdKZfVUqaiqGXsSCESg
51iMt2CNfzM+xVmNJ/7q7yIV6fPJBbw9BigJTfLwnHw7FZ8ErfU8aAK08d7Nm2rIKUdfxcrM07Te
oDHQms1YgpyK1oVBjAgMmgXt8j3HmnYtq+NlsyPH9zOge2CDYvQXvfUe+IL4Y4aVpa4LsMFHFy9e
/C7xVfO3fuu3vEfeBZBNPwm+P/ysN+jCe1gAYnr4QXkrRFocDS1rf+Q4zaj0F2AhYOi9vVhJp0QM
5jxsgSTyl194Qb14+jTmr43lt75/uHnPHj+uvnTunCpkc+OuQVGbP84wxOty4hj9KiY4pB/qCe0/
nhUgIt1GIE+mqGqDvvpBY0/9LW21oZsw/YjjCErdJCL763ZHvd3tqbbnJ2v/g8qA79kTkGnGuPuB
38Y54FxwTp7RWyEFDK4J14ZrxLXGcA7MAKIAapEzAHzdVxHLykx05MUBW6PbZknsRy/W5g1aAE2A
NkAjaR7dZ40FKGgKtAUaA63ZQgH5cqKPvibQ7FC7r1wu3LPttus4faACE+3naFfRfIBJW28k8cuD
bhJK3Wftb5H2j5p+zPQGWQTw779PF51h5icJCDhjVAT2h0q1yXSsSU3KAqBAkjca8SV8Mltgus2W
y+qrP/Mz6onlZXXx+vWgEhA3e65YUk8sLarHZmZVETeXtIVndvrJYg4vDgIq/boQ6sufGPnlx0pR
x/1jvgigWQnwYtiapEH/aW+fNH87Pt9ABrkMbT2g/T/QmqJK8tmUo7ITQKEqeYTaXbgAsdh37Fhh
xR5WpE9/fzAcqH9AoFbUw/ui7dqPtWKHF4FrhK/9xWmbLIGMSInGU2qcs2cAUU8HFnk82XiOoyVG
grnh7+lxXyG8uMAdtG2jgWecScHrs0QnX33u+UDLX97YVDvtVuAqoBLwNAmGx+n1MmlmSxwrcoeE
FYnXWQDwPXQQaPT9Brl4Lcu2XSd8QPkhBd6kr/2A+OMrxCc55hltBQRNQtevX/974q/9+10YdF8F
gGz6AfObhT90gZfoYlsI+JEAKNI+TX8DFB0uY8cn6Tiw7Vos8EPHGGgLwISFjqYIsZ9Fz0vkoz3z
2GPqNAmBPv0ugjBpCxUV2lwcDWPhQd+s4U5ohvFFyasMQinDJB0LBFm5Z0wUYjr3x1OFL9Aafdzp
xBh/whOfwCwANJ6v3qF1naOrO2Hbogp3Mmp/VwFBWf4r9nJWHc/fWCeN/85gqLMpYSbFigG1GFGF
6L75wbUuZNPqZQyOlSa0CDpaSpjyEYw4m/bhMBBpykcwodbYtYjHAUQpsVAgMbgZ+gMBvmeOHVdn
jx1TQ7xEpn6WXkOZrq2n/EQ4ggFQasLwWgQAQbNEu744h2EqVSMXtunYtkO8kAb9gw9QCwO+AH8Q
nzwjY2aIBXCTEL2PtHn7kXQBkpp+pO8/Go0wWejvofH1RcMPCpQZfa9FLzdoq/Vte8PLZOpRPTXi
BvV6vChFE6RtErMepQSiyqXTqkoStFIshBFex45Fd6PAnvD1Y6O5YmPA40U9sUq0iTHYKlYN6BuE
wcFBtkDqxEhXYMoH0eJ48NFPmjtgCAUE3K6NXNWVefCDKvrupRko6fv6Wrv6N2uygCcxtjAJzIr/
ca245rpGy/ESRq/FEJql7zUxU9GLBVNj98qcRyirI8VcwygzwCEEJ8wUgXZAQ6AlmwN+xnh72zfv
V/g3aJYb2YL0YTa71/b9ddA5YqZhVtBRmg8QFLTBH+ATWTL/oJuE7mcM4HZNP9D+W3QBW7hgjDGm
DdFQqGOovib9XSMp2xhls1sjx9mM/DUikiFMeXlDRcOIJ+GsROtw1Lftj4EaODA1NjXNnL+I5Np2
XKrLoMLE5F5ZjuoFnWPjmXZelALzpYbWhLrdH6jd4dAw+5O1f2xMl2C4DXJLWhJT8AHhATAj47c2
PDeZ2WOCwI/LBSEIcM24dmWUUfPnPAHSEiICueN2an8SJn2c3lOTAzu1pjbvcVQgJmiC45e+xpaI
MhB8NWydKBUvwrKsmMIIaFYHo/0w3L9DQmCTaH4XJj/xQgf0Dz7Q/JABf4BPkviHm4TAZ4+cABBN
P7+V1PSDyiaSbm9CyCH4QRtZQTbmmHW1/1ODACCfZ6+bTm+4mcxOwDhcU72/H+ZUzaYXM3UlJrJI
s9JWVmJgy5JpKCWn/wr4rlhNeRgDiHL7DP9ttKGO6c8fM79nYAFoAtojl0Rq/xhYhW+4IwcIhYbr
q3ZS7/79fIhgHX4Lv3kws/tmg4FxbaEVgGv3JuoNxmvkydZpsx7Alw1RXKLsxkFCvDHu4rg9WsRj
RC2/6f7ZIoHItGROqLISaAobaHWoS9iDPAbS2dnsTi+dXstkMhAAcHP3NP27qfCRC40A702zbwb8
BL4Cf4HP7qcVcL8sAG76+fkDmn7gt1wmiWeHAdDA5+nSgu7THvZ9HQMS0ul0y69W6yQWt8dBN5Km
zaYa1WpxhGBzzp+c5y7Rga3QL2RgJytsTtWfsUTTh0R2tQwoKz8WfJQAHtI0VjL/75tYdWqymQXX
Ru+7XsIcwwTfXx3gEiDxNPJDgeKZLkACOnByWDAZDVju+fj4rVFSvMJPSi8mv49rHk4I2LjwVBI0
JAFlWc51CIeTWHGcfzWGVrOMe+xHU36tCOQjog2l54xygY+kKVn7L2hDBopBq6DZqDMUQdNUasev
VHZIAOwR/YPmdzX9d+lvDgrixy6DXw5oEvr5+90kZN8P7Y98/lNPPfWNA5p+YP5fpPd6Ov2BceN9
K8z3N2gP5m/MzMw05+bmOmpqqtGz7W0/aq6hBW231YAWNQY5Lcx0S6KzivbgsfYK49HB25YfZQ1C
wWD4xxJrX0j6GCiFpa0TDf0l8/wxAvZlHb83xv0TjJMKoOoFZLWKFx5NIPgqPz75l56ngmy5f3Af
wCdxARL6AfBbKVn4olRcYE7EEFQclhtFTDiGryZLmBlQxPNi+Ae+OSU40uxueC8sLwbGYmIbcENW
HLffj4KGgZtg8URgKz7dSQN/xEZ8Mc1p90K6daBV0KzneVEZcMeyNkgANEql0n4+n98jHgDtY4+B
mH3NF7CMe+AXqUiNJqFvgN/ulxVwPyyA1NTUFJp+vpZ00nQxKNB/G0UPdOIIevS15AuCfjCJisVi
C8y/sLDQT83MtLuZzKZsNhlBmGxvTxbRaDjomE9uTICNSoND7g8n2CgrNlzCVrJ0N+xdjxG26EWP
pfyilNVYi41RbyahvmLgnlqjVVOOKkYgG5N5/ztpfzymEPQ0Jhz9xI1ABxUKCSbFb00dOBEn2Qrw
jfdxzbj2WMGV500AiPqiKctzjQCsFPrGFB/fmI0Q3tPxNdiyUFz/E043sgyaEfdbDgphYeDFpzbh
s6DVkW5jZxcHrm16enp/cXGxTUJgD3RPPFEDH0AI0B5CQOnBwW+Db5KUKfgM/Ha/MnifWACQ2V45
e/bsv0PzgoT70oAfEAAbxPBNujAPQQ/aSBhageaHH0Q+zT5dUIcubFgul/tkDQxajrM5In8pipoj
EFivhxjrBhNaRotwBBLKxUIx3SkrvK1xE4xgbivBBOXfDAJRStebihLemF8qz08Jv9Ydw1+NzXSl
Zsnqm7ad8RkeMHE49r4hFBboaclKwAAwzf97xQNIOhb9Bn5r4QBmj4GtJggGfh/XjGsf45+IgKor
YgFqEm8w5oJFmZVwfTxdez/ukBRIT0azzlg6TBSAj0+b04UcKxKtv+Yg2eBwmlZBs0wjXja7QRpv
g5ge9N0jU75bKBTAE1CCdS0EOpo/UBPTBN+Af2QXLfhLNwmB3yqPggAIgn8rKyu/iuYFKbF00w/W
5Efa/EfEExfZxEXTRe7SRTToe63p6eneZz/72SEJAdSUDLul0pabzd6KptygKYjMqsHOjkaM9SNf
LV58MjkjYNxCLDqCZJWgJbWtFS+ljUpqrSgIFPXoRzRvTsZJaEHVR/G8MRYeZwmqJPUfy2ZUwRBW
k4IgWTvPkGY7QYyUS4jaHwQLdkcXIAlwRBwLv4XfnLFvYwUkBAH5gWvFNVcDWC1RGCXWKCZIRSxA
TkbyZckzD3GNYOKt2D0cNxdZYsJvvNpvDAY69vMnpl+LLlIl6NDj/D/RKGgVNMuuyDCfX+8UCpuw
fp944onBiRMn+kT7HeKPuhYAdfCF5o8h+AV8A/6RTUK6lN4Cv92vYOD9sAAQA6iYQQsd/NujxVvV
0g3Bjj3N/LjgBhaBfP/u6dOnR2QW+c8++6xL1sCoUyrVe6nUelQLgE6qvb1oYWVUVwZmAr+fOwUl
gqscN4aqY8vWhGKNbQJdpOLrABBnDH051CNWxutHOIQxDSDAPtgHHBcFqQmwSoveO53NqjO5bGIQ
MAIGSUgHAlbrObpeaGPLRAb272PBmCEQ8Fv4Tfy2nZD+85Ux/MQQBrhWXLMlZiH4Blwar1kkEORc
BNkO7LrjLkFj7qIvJvn4lkCGsCTWv2ZwYAZa9kRQ2ZKFUYK+ZNVklDXSigq06uq1whHbqdRGv1Kp
gbaPHz/ugt6PHj3aBf0TTwTWMPgC/AE+0VbyKviHgUNlUB38Br57JFwAkkgb3/ve9/795ubm25BQ
tEFqeW7IHK/RhSDF16INJg8utAYXgJ7vk+/fWV5eHp06dcp7/vnn3fn5eb9arbq9arXehgDg6DMd
C51V/c3NyNfyEubmSbMssgR0yaYdBGusaPqrLwyDiL45LkBPvEDTWNEcwnHJpzfGERQZAU9UA07W
qfsJBSpeREIwqV/O59WzubyKDSExBYFgxgxtP5tOqbPQ/pYRs+AqQ66dUfeOChz7rjkPAFYA/SZ+
G+eQiTF/nPHjOXk/uEZca0lYY7K1OhEvIbamnq4FYnxBa1yhyBaBbUfz+nx9L4P4D0f3RUjFEoLB
0viBtqYZSwaSzTHyoo/DE7Ep0GiAA+C6UWMVmf+3upVKA7T93HPPubB0T548OQL9k1uwr12BGvgD
fAJ+Ad+Af8BH4CfwFfgLfAZ+A989CqXA/tzcXKtWq33Ybrffo4t5UUMc/WeSXsh3rtLFtGHaaAFQ
0yYPUiG9I0eODM6dO+f+wi/8QsCrdLF+uVz2UtPTnXYut0leVM/x/ZzSY8L629uhRqDNAUMLf1+W
frK09sUMgeBmYFQT+Z7oMsNrniWJwlJy7nwYHQ6DjCGCrDs2/XX02RJReaWZxRITiv0ITTgUEJaK
Q4L7oq9+hs7r8/mcmqWD/rjXVfWRe6AbsEKa6oWUrU5aoTluzgVIagIyD+OJz3haUyX2AsgSWtH6
it8s0ho/R24AqSP1Dl3LGsOBywPpQptpEhbPE/OfyeXUlK7V56i/pWMB4/p8a4zcy4E2JwwYepq5
ebpvmKEZ9wAE9f86M4DS3QBx2LLHwz1UPAjs68rRsMrPCZ4ro7chSiczjSVAgHs6+xDQKPL2+p64
ltVvZ7Nr9tRUl3jFJZr3aHPr9br17rvv+jdv3nRIs+8RcyNFbutA+QD8QS7AK3TMq8RPM8RX/x3x
R4k++x7x2ofgu1/7tV/zyQ14uL0A5L/7u7u7KZJmJ3TQ7316+b+g4w+LSEJhBFOHNjA9NP8erKJm
s9kns39EFxKRDJlFHoKAhUJhRD7TTT+fv+b2+0/aOgA3oMXtk4mVW1oKzC1LpGjkdFZf5GYDBpZB
C1+0xfrCHLRitWGhgDCDRpalR1SPKw/HRDBOMymTIWOlxCJOoOLAHlVihBfIPD5J13RjNFSbw5Fq
0HUyHsAM/f4yMdwiPS/TGTi+lzDz3j+wCeiepXtCnbuSVZbo/6DnZ2xgFNgKONZrdH27cNmUxgMg
JlwkK+FYKq2mMmmVdkSFpYYKH/v3djgr3LaiMdwxABU9ZNS3wqYkvgeo1w/uSQAhbk0gSNnWWLBH
RKDdPku4VbZYLE9/zxJ1BbLXIao30KY/zhG0CRoFrXrsvuTz14mWb5FiQ7lnVPI5OzvrP/XUU+7q
6irxdw8BcgtAGcQnIzTN0XcLQZbY92/A4KLXHqff/yz4DNgZ4LtHwQIAgIFDJ13M5/Mr2vz/LjH9
Bl0AKv08eg+RT1gAaAJC7r9NF9Unf2gIk/9XfuVXYoVVZB55uVyuv5vLrSEOkO71nmSfP+iwWl9X
ufn5WLOKJRg/lsLRxGqzuQ7twVrFCk09T79nBYmhUFuACH2JHGPJUlc/3twjocR8b3wevp883VeN
Zx9G8OZinBgqPOZSDjG7UiMi7CG0CBEUuslQUZbSwCHKsDAmtL8Jh3WXDD9xgyX4imEFBBoacQBa
tyrtK7R2jxGPugC+BHoOnX+a9hAEgTYW5dp0NfSaNW7+scaNPJYyph7JCdAaB8DiPgFLAIk4bAlG
BKGLvfzIzw9tADuK7Nu6f8QStf7R81iJ8LgFXWIEjFGk3IA2o9Z1WKmYM5DNbuxmszfJShqAtnld
X375Ze/KlSvq6aefHpJZHywoMgDEJ0Pily6dM5Cys7TGaBNwNF/9DL23An4D35H29z+hjP9kMQC6
CNTzY+pvhU5sik56h7aPUe1EfzeJkWu0bdPfNR3sQEVgny5o1Gq1/N/93d+dgO4h38gjKTf0Fhbq
rUzmRoCuqhmuv7+veuRjMdZeIGWRGtQSeCJgZR5cdrVFQV8tIMTYaBm5D31/2eVmi/y/L2bh8fQb
N2IOzmJEE4Aloq9sPJImuxYaOCf41gV6Xka/ui4Ct31v0jxP8tN9P2bp3HMhkHBr4s1AfmI60dLn
hnPEuQbnTJ/LaE2qjJHqysADMKHBlW+soY4FSQzAWPMTM7gvkr3BvfPj49utUIiH2n2cAjC1+4FZ
ET5XaPnRKIr+42/QJmg0QLLSGYD9dPr6aH6+AZoGbcslJ+XnE3/44AfwBfgDfAJ+Ad+Af8BH4Cfw
FfgLfAZ+A9+B/x56EJAkU4pOqgrAAvJTPqIT24LJT3/v04Y8P4oe9gB9RBfYJdMlyHW+9957SQXr
PqwC+ozrVav7rXz+JmnoXlg6Gk4L7q6thUUWUepociZ7pLGka6AjuD5H/wNNr6PDwZ9OSBA2t4nK
QhAviiJHTT6yXkDFx0v5QkMy0KUUUJ5E1tVCQb7mm1BfZjORcCnUQdr/kxQBHVQMlGRhyHNRKqFB
R8WQhKNRX8E1x1+Tv8HgoJ50s2JNXPEKwQgLkCP+XJot76UdPse95vsemo9hgJgrSC0xgMY3LQHT
WtLKCTQJ2gSNMmAo6e4+McEq+clN0DRo2yTXb3/72zD/PfAF+AN8An4B34B/wEfgJ/AV+At8Bn4D
3z3ULABJH3zX7na72UqlskJSLNNoNP4rnTzSe13aI/LfRlpDhSOOgIQyeu2117x3333X01J3Qhkh
QLKwsOAiFrCXz68Oc7krUYknzCykWcjUUiIdmJSvjqxAGcDhvK6s/ooKPcaaLGoa5I27yaKosRXN
5lNKVoO5k2PKo2IVjWZjBglNwBHRKOQaA0t9AyhTJfn+ExmEuy/5Peh9/4DfMJt/JiYGa8HtmQCd
ooYi9po3npDEVoBMtTFk29iasETsZXwPI3guDu+IXpCIj6P8viUQzOKDPjib4B9QExEpIaJF0CRo
kztB4WoO8/lrzUJhlZh5AJoGbZv0Dh4AP4AvdBUgwic9nTaHMGhpfmqAv8Bn4DfwHa5S8+FDswDQ
vpQn6XWa/P+1drv9ro729xDFRNUTShxnZmaG77//vvvCCy94v/Ebv3FHlTQ1NTWoVqtDsptudbPZ
69waisXtN5uqd/NmmBo0er0jjW2kbiyO5HIpJ2sF2xIdhFbE6CAt4MINIHDQtMLCRo2RanwJMRX1
G4i9rkiLYK6NCkbuUVAJ2m9iuq8x/Sdp3LWX0PRzEA7A3f59UDOR5x8wTt2YGuQnWAHSCpJQ60kT
hnntlE6pTayxL+o2vPj036G+d+E99KK0porSwXGrIPLntQVgSbBSKQTkGDmY+trtA02CNj3XjRRC
N5+/vlso3AAtg6bvZG+BP8An4BfwDfgHfKT5qQn+Ap+B38B398OC/0nNCItOwqrX64DzKhYKheP7
+/uv0uu3ILk0wk+fThKop4G/D8bnoMsBD48vCL4SLVpvfX6+tre+fq0qcq0eyoxJ2o5oD+y2wMxn
5tc3JoYwY85xBwFo/wx+oCti/10y3+rkw23tNdVuq6U6g35w7BJ9ZzqbVfOZtCqQ+ZhSohosNqba
GkNy6RoBS9QIxFKEbjhsVGp/laQpE4BGTZj0JO3v/wTm/Z2Cg1bSd9jt0dH4iXNm+HUJncURfbYC
XK2BOdUXMKMTgG2EYRdLwJ05YdOOmOrL6VjUnQLff3tA95H2LQ0XV8hk1UyppBaqFTVdqah8akz2
tigW45qRKPIvW3/9yQyPr4XTSNMkaJNrVPDN3Uzm6mBubrdUKvUN/z+xXxtBU/DJO++8g8ag0TDA
icCyBEC45F0Mb4HPwG/gO3qvBj5UcgLOT0MAyOADMTQJquzctWvX/gjBCzoxpP9Q9guJF6Cevvji
i56MuN6JNOErFYvFUbpabTXy+StH0ul1x/OOIBqe0unAwdaWShUKAbHYomwzSlHJ+ICO/kc4gkrp
6H9YFThADrteV+dJin9EN7LZ6YZDPrxxFSBSREv5nHp6eko9XiqrisyJ6xvu+aYgGpcte2oSqMIz
8P19gfDr8XOJgGRoUeUlTSW+D75/0rESZt9FqVDpZulcfVQ4o5nQZiuAaYCFXPC3qATUv2NzfYLG
/QvgyJ0wz28rJzYhGU1CzZGrrrR21fv1htro9uj+6vuOe2yD9hxVKeTVk0eOqGeOHlXLs3Mqmw6r
/yxNE1E2gF0IkU6UU6mjAiBYJqBHokXQJJ672gUYZTIb9Wz2UqpSaYOWk/z/JAEAywj88vbbbweN
QUgPjkajgMHBX5ubm39x9uzZ3wbfSX586623/IfhAgTdfrRtNpvNS6TtA6gjOlFsEfOD8WW6JR6z
S4wDeCdOnBjBd9orl1cH+fwF1oqY3d5vNFR3dXVcFswNIOJvPyFoI9FbLG05dIcD9e7N6+ov3nlH
/ZCO2QSOGxeMiI5BGJG32h31Nzduqb+9dVOt43OiZdTjEeMMUuqNU36eTvGNtfuk728O4pCmdDQw
RGQXJiC7jOq/u9kSTf7bbAdVBY4Dmt4YGdhwXQ66xsgK8OJuTlDcI90rttxEYJBLsnEvcE9wb3CP
9FlEsR5u9cG9xT3GvcY9x72XaWE/yXrijM9taA20CJocaeaH5dIrFi81SqVrpK37oGXQdJL/b/CC
Yl7RfIP5gSPwkwpnCOyDz8Bvusv24ZcC00miqeE8LB7k/KH56e9RPp9HpN8386x3sAAimiKrYoj2
4P7S0mYtk7nM6cCAONAhtbERDl7gGyKZRvhvkdnK5yEkeXc0Uj++fkN99/0PVaPbG0f9xC4eEQz9
0guNPfUKWQrrva7GJbCiwqFxqzA3jIjAowAX9ROCfjLOoIQlEEubmQyWgP7jJ6T97qYw6HafS6wu
NGcbKDUx2dfMAqiEoKCvRN5eBGuVhnOLeva1gAtiNrplG/cA9wL3xBOd/hLeaxwBDJ/gXuOe4953
eZwcuwACSyJGQwIcNcp86BJ10CJoUun0Hx476fQl0O7c3NyAtP/gbqqxJY+Ab8A/4CPwE/gK/AU+
A7+B7x66ACB/RJ05c6bUaDT+CqkLxM6IcUdTU1Mu/P7f/M3f9O+B+SXd+ToO0HcLhSZJ0svkU6xz
JgDz2Qabm6qHtIs2w2LSWQbdLGvSf4U4pc9fIdPtlY8+mpgIyxQpR4uZKcbrrZZ6Y2dH7ZO/GUT4
J4JESoNV+JFmnBgjLgNKxpTfJCaP5cxNE/1uff9PWBloujGyDiF2jknCIWEqUsysZuz/yJpg2C8V
C/J62irA2uMe4F4kpepi99BYGNxz3HvQwMAQopbR8RebAyGtTAT/iAZBi6BJzgAM0+mNeql00SsW
m6DhmZkZeWvuSgBgA/+Aj8BP4CsVDBfK7IHfwHfgv4ciAMjf8Or1ug8EU5JEO7Va7SIaG+imDSGx
cNKIaE5UWd1DIZpuDBpVKpVuc2rqWjebvRDlkHVVYPf69bAQSOdefWNUl+kHWyIG0ex01Ds3bqhe
GGiJ5f+CoJMaw0iJQsXYKzA3L+43Iw3vRfWznE4a48pxsZIlgmZeDFTEH0N6aYEhI/uuEXmP6gmM
5p07IQH9JNWAseIdFW8u8iR6Mqf+xHl77JZw4ZZ0H2A1ScAVNsPZhdNraI3zr8pT45Qd1h73IH6H
zGf6XtqT+UDce9BAs9MZM6AZpE4Y58Y1KaA90CBX/3m6+q+Tz19qlstXiX67i4uLw+eee86722U2
rQDwEfgJfAX+Ap+B38B34D/wIfjxp24B4Eenp6dHN2/e3KWT66G0Fz4LThb+CwIadxn0U4YvFNAN
cqbHjh0bkPTstWdn12AFMJOg52CENkmSvkPyvTgaG58ma6DEsAlH+xHtN5tNdWljwyAUwfK6UCju
DyjRCmqp1nCkLrXaqj0MgUosEdBSeoyXF+WkrVgqjJtcLC9eyDORc5aZA1mQY/r/t/PbDfVjhqFv
95kDYwLG78aq6IxR4hMuAqdoNayXJQuoWNPrmYOWKKMOi/3CVG1brz3uQXTfZDFHzJ2zYyJcCnbQ
AGhhJM184bLFzp/RnrUwB+2BBkch9kXk2pD2v9ReWLgF7U+KbKiXMhYDMP3/JEEA/gEfgZ/AV+Av
8Bn4DXwH/vskzP+JewHw4y+99FKwGDBHuMDnTo87dDBFNTwrKyvIifZuTk01aVEvLNXrN6zR6Bgm
tMLkQucVAjDpajUgGCcG/+xPNLJE48ZIem8At53nylnjBhKfocN0a+i4M1BrKM+PgYlgqk9tNFBH
U5lIQ0X4A5bO9Qcz81TUTMQAl5ZMI/rx3LZl5p8FQVpmEO1BRP7vkBGINf3pnoBYrlxmDtgVE3uL
B3pymjAQlI6uzQhaQ8NUoT1uxAoFQnjBWHOsvQT1sDhlqKTM5gIhMQhE1PqDBkALTxw5ojLp9HjK
rx+v7JRuQOCeQPsj+Ec06PJ8A7in2ezN3ULho1S1ug/aBQ3fjfmPxx/90R/d7u1gkUgYIPXuY2rQ
m2++6d2Ngn1gAoCFwH12My3TDSiXy+1apXK1kc9fXGw2j2HBUQMwRACGbkLx9OmwsUepqOkkBhZi
4AOgu66hzb5YnXfU7MF9JDptiJ5yJRpB/HFAaOh6ah9aKJuNhIRnTZbORk1D1tjUhTCw1ST6DlsO
UUqQQS59f5Lh78Hk9++iDsBsBU5qDU6qBfANAYFztjmv74yn+MTxGvywEcpWUTMQTyIOJwEJi8jS
PQX4gGOp/e4oWHs+SUvgAoSp3nhTmCXLAI3JR6CFkRZiB8ZVIsxHN4D7cgHTRbQHGlQ6LgVm2i0W
P94ply/DVIf5r9N/9+qJHfh4++237yvmu60ekcft3ACYUq2Zmc2bhcIGFwRhArBHGgAADF0UYcjg
jFlZZxDsKJhZ78Y0gRXrIrTGmoOjyQYmPH8OJDJ0dbyA2099K/LtLUGgStaw62O5BzTX+LpWwZPV
d2KcmGfYlaYbcDfpwLtNA3oHVAfKc/AMgIzofSkcjKChK4JtYxARP2LkaMW0EI6w+Oi/oetHHf7m
fbGsMaSTFXMHrMR7DloYcSA4ocRZiYYfrkgFzYH2QIM8jRrXXSsUPuzOz29A+8P81+W/92T+/zQf
j4wAOCgbwG5An1TFrUolU1taitKBQTYAwcArV6KgTEwIGClCJpSgTVVOEBYCQliLY90XaxTQJcTC
ogh63H1Lt8aKoiTFvQhs0kezqzWisRqny6R5b2h/OQvRP0BD+XfIM90pFXg37yf+jlEuKyswOV9v
8cQmGcD0xxbROGCr23U5VSpg38N3dZCOvoQ1j2lsGeSLq3wlJ5YnYSWkQzTeicpGZcaWtOkfNKUR
zYH2XE1zuEayUtdv5vOrhWq1Rcx/T+b/oQA4gP4QQc3lcm6z2SzaJ0787NbMTAgVDgEAyd3vq96t
W6oLaSxSMXzjlAhIMeOl6WZPF4vjYJzIA8e7gFSsaSgKHrFGJ6JL03eqMP8tkXayGGJaz46LkGRV
WM7KPQhC83tKxUeQCZyD+MyBeKzgbnx//5PehNuY/7GafGl1SeBWKz6yS9bERiW3NpdRj31+W7f+
Whqq2xfOPdY8bYdVfpYl2npVvMknluIx6kD43oMW0tpdibUtc7MZt5/rFmDQGmhuFMLeR7n/tcXF
0o1cDrj/3eXl5XuK/h8KgGRFFFiR58+fB07GU5licXG7VFL1QiF2Qwa7u6p39WogmTk/a46XksGo
bDqtFqvVIGiolNEpJojWMl0DI6UJQ24KdeYAuHTsMRQZH8h2woHVfghG6rHg4CZC09xR8Y461v4x
wBP+rACouBdG9u/TZ+V6Svh132B8z8TxN47tRcFSHT/RaxVOPw5huqI0PgNyApGY1hxrb/nx9Fni
vZLC1LjfoAHQAmjCN8q7Y2PdmK4w+4JoDTTHCgeCokFCZHdurjTIZI7u7OxYEABJ0f/f+73f8w8F
wD0Ig0uXLqmPPvpohsypf08309nL5dQNumEMugATDJK4e+OGGvDsAAYJERNnZf48RdJ+mSyJs8vL
4yCWgf4SaxmWAUUREyhlMupUtaIKgTsx/p5tjyGobNEEEwHIaENAon9HBTCCuX1D+09oXI4TiFiB
6ZvfLiWYZOInfcc8lid+1zfOKeY/i3w/Q7PFAUb0GnhjcNZxGlWFaWTt6du2TPVZwZpj7XEPYj6/
WbVhqdg48KjARz8HDYAWUgJ+TA5uiZhf0xVoDLQWaH8IAJ37X5ubU51y2VpYWPilRqNRAbblo27+
/3OIAajf//3fL/R6vWfIrDoHcwvgAqsk/ffRCaiLL0YIBtZqqkN+mYtYACwDvbFZZ4kxTXhU83n1
/PHjqpDJTBT4RBaACASyyW9ZKmofXSFr5PT0dJh50DXc4Wd1SykzvyWgp4W24n5zRiYK/vX08BBj
jFVsCrI1diEs4XP7E8NQ7k67363mj44vMAEtAcM2MTU3KhbSXX2eP87D+2O8hvgMBztCXOYYi8VN
PdxQpiHGsPa4B7F7ZccxHiwVPzd5r3HvQQOgBZkxsoQrIGkJtAUaA62NwoG3AQ3uk/VwgyyAIdEk
Mf6p/f39s3/8x3+ce9TN/0c+BvDKK6+o1157bebYsWP/C/2ZCWYP9HpqkwjgAt003JSgAAPTWIDI
QpIZU1kYJozjASwouNAERIuc76kjR9S/fvppldEBQVNTsLaRmoc1/YlKRX1+5YiagvmvdP4ZxAlN
In1NK+xEszRBynbosCtRxeoQYl1oPMAymmCkQUnFRJswaKaiLVak4I+tjHtNA8S+I44X+y3xuh9K
qfAc5TFk2Y0A2OB0qSRAWxdSWXrNIsESmf6O7tcPj4m1xz3AvTDvz9gCSLDsQEx0z3HvT3H+X2BL
yDmQ3PHn6Yk/AY0RreFvWADAabxcLqttpKXDvoLM0aNH/+fXX399RnfoPbLm/yPvAnzzm9/MEFGc
Jan6GRTv6LkDqk435KLj+EPbHkT9AXh/e1t1yD/ztFCQNdtRRFeYdwW68S+RBvhvn39eTRUKsYGi
lkE44yySpZ6cm1X/5sRxdbRQCvvJ0yl63dFWqB0FDFnzB5FuLRh8EUMIEWvtuFZX8Xy1JdyCmM8t
fX/LiufiRfosySLwE+oA/Nto/AlrwUyJGufF5r4l6ytM60Vfuy/WO7IuGOU3Amxlf17j/WOtac2x
9rgHuBe4Jyxko2yNEexjIYR7jXuOew8aiM0nFN1+MvKPDbQVFP5oKxPfadPxPiLm3wOADCko0Gml
UvlX7Xb7zB/8wR9klXrgLRqf6JF6VJmfpKW9trY2+9JLL/1PQEjlGWnBhBR6vuY4+1uFwtWj7fbz
cA1sWAOYSnTzpsqvrCiLfDKu6rJ5RoASFXaaufKkRV44eVItkhR/99o19eHamtrTgx0t0QziEPEt
Vcvqmdk58j2r4WBLEAL9ZwcgFkRbgVsyVG4qLHyxfPqMo0te4cs6dvhZRieKOuHGyMWu1oTc/OJH
gkL4r2JvFuSYtQ++LH65l6CfFe99iKU2lZlqU7HqwKgzUgbkgBQcrKMVN/E5cKoxA7BGlsZsDDW+
EwZYUyFmv5VKhZYUPoP1pNdX8lX11WJJPba3p87XdtRGqx3rGeDfgal/jnz+5+h+H5mdVVkcy8z3
B8UZ7rjeQguA4c5OQFugMVdbl/D9yRId3LKsjEuKKU90CQWVSqUKJ06c+B/ffPPN9/7sz/6sC/DP
R1H7P8oCQP3Jn/xJmh5PTE9P/zykqjl2rJvNvnbLcepL3e4ZYn70TAbuQH9rS3WJkdNTU6FWopvs
6SkvUakvV31pJs/R8xMzM2qB/LiXSStsNRpqB4hA9JtIRRVJS8wR8cwFiEA2wNqj2W920KseouEE
RT0g4AC1xg0yWx7AKBw7AAuxfTsacGHFBpuEo6kjDHtGlcFn6JosUVrLNQKxeYiy3VgyqrAgTCFg
9gLYCcxvm9aQwewxQcHTc6VGx+8D5EIPHrHFrEb26ZVowMFnIwAPR++jGIwTMLyl4cbD2EAq+A7i
AbPkz1eLBXVuaVHtDIZqh+5dGwIa6MS4d0AEIpqYJkEPoW+LEXLB9UDb82RpJcbB6+AfaAq0xS4n
Pj+y7e61dPpq3fOeSuuBuNgydC4zMzM/Dyz/P/zDP9wiAdA/tADu4UE32SLmr37pS1/6NcxEB/OT
SRVsekoq0IW/RwIgv9LpXFghKwC14zaqsiAoyE/LwbdbWgoJWSOt2AL3PYZRhz4CMDrduDxp9yUi
Elc3HOG4FhcVBSYh+X5DXfyhg06ByaqZOghQEfN70C4c4rf9SOOPbO3LslAKLALNEBpMJPyKGH8u
GMxidBo5ClsdUOYrvyuEwEFZAMvU/AdpfOMzvkibRp2QMv2mNXyEtadTpjYHQrXZj3VI6XsUMmjI
3KRSw9IJDqzqWIvFQVktRHLkFuRIKMyUHXUG9wS/S/sU3Vf0jwRgG7gv+nwia4mtLfb7BeIPt56D
pkBbMP9hAWBNt0qlj2rl8j/1W63HSfjnQJ9ZEi4QAOS2Vk6fPv3rb7311od0flvf+ta3DrMA9/Bw
yI86ubS09IvQ/jwYkSek0o38MS3yjd1isXa1VLo2JEnMQT9EZ4e7u6qzuhpgtPkssTkVGDGyyA6I
0mFLNxVliHDydCORH0alGNJEtu4DsDXB2U46gJjmABVnAsaazA6IPSBUTbjwe2G2KgE+EVojHADU
8FRaEPAxfRFUlMzmSxgrcyiK0MayrDYW5xBa2zfMeFPrS/9d+uxm/t3ndZDXwCJDX2vEyMzwgYlv
j0E5bS0odAbA4u7SWKDV0ffAjt2blK70xL3DPcS9dERWhiP8MtqvOM/PNf9a84OGQEugqZH2/fHZ
geN0L+XzFzuVysekXN5nK7WrLQHQ6eLi4tdyudxJFXY2HAqAe9H+Z8+e/RpmocvpqNhooYGT9qf0
0TYQX29UKjvXK5UbroYLC7oE8XmS2IBqDoKBunwz2Niviw3q9GMFIlZSgI0RYzRzW7pd2HK0VomE
ghOYqI4zhkEL/FjbjiHOKhYSkTkb+rlRNkEi1PBze5wi8/WMA2X8LYN/sdy7LCc2xqV5gvmVeN8z
jhUd+4DftsR5Kvl3JOgsfY36M3INBHJzuHdES2zYFsvp1uB1rLmj74E1FhKWODcT1FMWAElQEk9G
/jWdKK04QEMBLRFNueHou+BYq6R4rpVKt8jF2Cdl9B+J4Uegzxa5jjzFF/R76tSpfwd6JgvAOhQA
d6n9C4XCyrFjx75Bi2gx88O80lHW66lU6ibdPJv8sXSrUOiuVqsbnUymHU1r0T0C7atX1ZBuSITW
wpFdtgBk45AEEDEzAEJbBn85YWDKdkKtFTG+EAQgSFsTbWSyagKFz+9oUzhKF+ouRmYOX6S9fDGW
mk1pW5jDB1UtTjBBkklvvGaZDU+3qa5TxrlEVoo453BunxBgapwRsbSF5Og4iCXWSdnj9YvqKuD/
w5Rna0uvcSAIePSYxKBIGuohwVTZtZMWAOf8Efgj2gENgZaYruASdrLZ9qVS6WY9l+uS4BiR2X+D
aPE6tD7TKuiWaNVaWVn5Buj5UbUCHjkBQNK09Pjjj/8c7VeCYJ/2//WCgk7/km4wpG0ZHwchbJTL
O6tTUzcDK0AXBg2RMkSnIElvj47jaekd1Qdo1BmJS+eb/rMcJiII3dbtpsF/zrg4ZayZQqIMA1Sp
SHuxkODP2FKraYIOo95OFKSSjG4JhvPFfMMJrSfTglJ7S3dAlu9Ks166CuIYseOK9eC/bXF+UjBE
56gj+rYokoquH3s05GjmZisKaxdbS2lpBce09KQ/4ZbJWIORhow1T8lpRYImXFYioD1ofqIh0BJo
aqQFx+Vq9dZaubyLIxPTZ+k7gML/K9AnCwG2AkDHmp5LhwLgzuY/5gweeeKJJ36HFtUG04vAH7Y6
few9YCTSZ0tEJMizuv1cbn+1XL7ZKBQ2Y4UbJMF7166pQa2mXLoZSr8elQprU082fcRMRuFf84RA
2xQEkamqCZU1G2sqZ+w28HeD70VFLaELwUzicCUbWw8sKATTsGZNEg4xt0FaL2ZHodDiE4HEhO9K
895kcqmx+TV57mziOzoAKoNxkaYXiLiROa+tLEt/lgOIcs0l49vawrBFHMOScyE4xcdxH3YNdalv
4C5CCBCtgGZAO6AhWVi2XSrVrpRKa0Rz3ZAc7DwJEtDjedAnxwFYCICOQc+ga3ID7EMBcJsH5p4d
P3788/l8/gnW/ryQEAC00G8S0wNhtUqmV5m2NGYQ0N/7O5XK9WtTU5dcXR0YmHBo3ECJsA4IDumY
rr7hnkZx8eV4MdYSsotQCgJhXnJOOtA+dpiiCjRWKh1qMMEsDge52A1ghuHINGtBsWdINVu4Dibz
Kx3ptmNlyNaENSAtARkUlKWxllEnb2p+X5j+tgxMsiAyhIAlBJdjXJt8D2sgXaTg9VTC+gWCIB2s
sdJCILDCUqmoRkLeIznFWB1wjyMQUs3goA3QCAf+QDugIVenmEFbZGle3SmXN6xwZiUw+wv0OqxR
/P0m6JbjVWwFgJ5B16DvwzTgbQyAdDo9f/bs2f+VGNuRgT88x8x0+swP8B7ty0RUOQxNoA1TVfsk
BfZvlMvucqVSXWy1nrHgr4GYkJu9dUtlpqZU/tixCLRSms6OJHjhAlhiWIVMndk6tx2l5pBiRAOQ
D0L1g73nhYTPwSZbxUE7bG16Bn/rc5UFN9H5CPgwxsVnbHxLIuzKAicDO18Zvx1AYQnT2JWISTIW
IISJLQJ9ngn2Kt73ZRm0jFEI4aX4eeQuOcJiim9OJFjsKGZi2fFR3ix4lFm0JPAgI0RfAe/tSYgv
kffvbWwENDMk2hkx89N7m9Xqx9eKxQujVKpOVzVIpVKY4JOj45Xp9/aIRn9Ah/0yKasgJQjYLmzE
+A7o+vr1639PVsD+o1QZ+MgIAJKShYWFhRdKpdKzXFAhpSgt7mVa5H1a9BLtCzqoQrTrB/MHMYJs
f3p690ank612u0sFz5sL/H4ijkGzGRRyOKWSygA/UBMeF9t4uggF5l8MNMJotuG9J4ZJjOv9U/Tx
sDgo8HVT4WEcxx/PCwCWIU4cxKgLlGTePiod1oLB09aHiafH48PZgrHkODR+TVcT+ge7W7FWWiWa
ekytH0X1zdkKxmuWWbsfpT6tOGNry8ERlhBbDQ5bBFGwj10A4WpFvRXjzWehzsI7SnF48YnRKmxA
ioSvqPmPAGbgNhLNuBpkBve05zi169Xqe81q9art+zyUwwlLNvw8nYNL17NPwuIy0evTsnCNaFuB
rkHfRMcb9F77UABMZv/mnn766f+NFjMjAyl4DvhjWrjvkx+VokXOkBBI0x7j0gZ0c1r0XcxUR7WV
fWNmZjTb682c3N7+t9Jv7e3sqBSEwNmzMDWUpbsAQXyoFnM0MShdbCNRebiByNTQUR4dhKwHTEBT
Re29TgBrEzSMuBA4XO2mwln3thx8KSr2gvdxTroYxdJFRJ7eKzH8hInfxA2MEIljk4r1bMSI2VVY
heh6sR4FZfj9tiEAlJz0JJmd3+N14VgHz4TUQbyouIfjAyJW4HNGhTW8Mw4iBhaAGs8RlC6ZJYuT
ONJvj4urlFKx2QQel/uCwbFM2j2E3w9agek/Eqb/2vz8D29MT/+I1qlORGgRk2dpzUth1jqdgVKi
bUDH/D599xzRrc1CQFsBGdD3xsbGm/RznUfFCnhUBEB2enr6yWq1+lnT99faf5sWF1sK45Fh+tN3
MIEII8h3c7lcjaQsBIEzymS6N/r9N6Z6vaXpVutlW5fSIpLbWV9XKbSPrqzEAmAgMJh4kRAwKuGU
AOqMVbdFaLZ2ZFEoN+z795DqI581nCLuR0Moue/f1laAL/JDgXkNwgRzcByCtbMuXIlGZMl+Aa5y
FDBcMaReAxKNr4/r6ZWbXPCjZE5fRvaN1xItBJEBiGUwZGBQBvhELCGs9+fIfzoQUkGGRBmBUBYG
XODD0GFmtSNre30vXVnrrxF9gpZyMvtBIxz157x/o1z+0fXZ2Tfc6elrOctq0Wu4ZRU/fJRAk0SH
EAL4exv0SnS7KOmYaFSBvkHn9NqmjhkcCgDcNlqc2Wefffa36HkBGl+aT8Ow7xrBP48kbZYWGpHX
ES12m/Z7tNXpdcwmABQT4MlH2wsLH9zsdhdK/f6K7bpLIBAEdyzkdW/cwA8qe2Ym1Eh6Gm0wmFEO
huCeARPmSvraoi/f08Qe9e2nUMevtRCKX9xQawXMj6CTzo9z04qnVMTEEozC4gAWjm0IAWZUR//t
iYo/af7GYgqxisBwCIon0oAqqbpPFujI7IMhBKxYGe8BWQMRLFQipy8zJ5FVxXiKqfExotSizFaI
xq1YqTPWmdOgxnQitgBcgSoF2hgQjQxDpRNsmPJzc2bm9e35+Q9Jk68T/bWJxrKaBul0HcB0gyZT
oE9ifFirbxLd/lvpxsIKICu1ADqv1Wrn6b21R8EKeBQEQHpqaur07Oxs0PRj+v5E9PCXLumAHxYb
Q0eRgmmSBbBL72MicYOkawsoLMVi0b0xHDqri4vvlHq9Iyc3N3/J0nXnqO3Hje7evKmcbDaYLgwm
cTRstdIBQdmT70vsPm1m+0agjAnSF119AYqtHeLaY3otN//YWgsFiDrDUUDnsgLPZgEAAtVML8uW
LR2w4mBcNBLtoIf+rajUVzOLF/XN2nHYGg706XOJAnmSKWP1+GOT3xY1/0rm5bnQSVoCOg4TaHed
DYlVRersSuDz+3F/3zLSkxICnoezWhwzETUeAYqUCPwxk6PDDzQB2gCNuDqLhPduzs29RrT0dqZQ
WJuZmcE0ni7RKYJ8YHSH/gbzEwk5cAGwp9vhXgLdEv0WWZkRXQZWAOgc9E6uwDas2E+7AIADNXXu
3LlfR9MP+/5S+2MxEeQD85P0dWnr09/7RMh1WvA67fdoa5VKpS5AGGlh8f30ju/fvDY7+8Nip7O0
2Gr9LIKByAygYcja3FQO3YzCsWNhLED7xjxbgIk6CrrJYRFiWCQLhFiajKPR+A65A2ElWxjpD3BC
gSCNohddUuq7Ah9PanwxbpsHavJ7kXugm4V87TrY2qKw1Rh6i01lT/jExgykCd/fF6a7EiXOSXvp
FpjFUhOlz0KLm+nCiPlTRuBPCUtC1xPIOoWoqUpOFeJ1EVF/TxR8eRpOLggSw+Uk07+Hgh/t93O7
73a5/NpqaPrfIAVTP3HiRIPockRMDV8/7BIn7Y84ANGlQxsyUw7oFXRLx3teZrNgoZIVUAG9kxXw
Ab2//bCtgIctALjp52tS+3PTjx6B/A6t6VCnXALmpxuIgqA6/Y2tSVK1gxHMmKO2urrqk4mWomPl
60tLF270+68XR6P58mBwGkQz0tq6u7ambGL+3OJiEKSTWs5mAuKSVQ0SEaXi1LjDji0CW2gcGVEP
U4kq6vLzbQ2eAUZGAFLk5W2t8YMINX+XmZ4hqgRaTWQR6OwFM4Ur4haWcFci05/PHdcHMMxBP6b9
zf4DJQt2ZC2CKGaaEAZmX4D080VaMKrui/oBtCDwDXBWvh5mdrH2lhSYMjbCwoB9fu7wE3iSYHzQ
AnH1WPvTZ1q53MUbCwuv148cuVAplXaOHz8OAdCh43jNZnPUaDQssgLA7KhFyYTZYYfkVipPQmRI
9+kdOs7TRMcppmm2AkDvRPf/NwmBXTgqn1oBgCaJJ598Mmj6wWgx6ftrSYyCiwYtLFIsyLsGfj+9
VqP3a/R+kyQqyjB7p06d8p566imgsfibm5utvb29Bh0vvzo//3ah358jm2uBLIBqFDSi33PI7AMB
ZmdmxlFlEAmXuAL0QZu10nxXcryVqAfgyLMl9r6uBQjnAQxDTadfD5gYgUBoHBA5B+7E1GBZqOQL
zR+0N4OYtUADk4B4WTjFJvEkoOPERntJf9qMA0gG10zryLSdiAso2aNgNDDFNLjsmjTjBIEwSI0j
/bK+n+MzUgiYyEZihDiP644GqzDGn94HaNIw/YkWAOfFgb+BZe3dmJ19DbSTzmS2FxYWGsT8rS9/
+cv99fV1/+LFiyNibB/xKNqT/vACNyAFMyB8ZIg+G6Bf2h+Vbi2sAHJV50D3b7zxxmVSfLVPqwAI
gn8rKyu/iqYJs4aaFg737Q1a2BYzP+2DoB9Mf9o36e82CoSI8V0SBAElHD16VL300ktDWvQmHS+z
5bq5a0tLb+SHw6kTm5v/feCvww1AGLbZVDaZf4G5Wi6HTMm5aCZaNsNlPEAzq5LBNiZG9kGRFmQX
QtcYhA0v45oAXzMsVxYGQgTa3BAAXPQTINCy9tdWgtJ7T0e6QcBRUYyevmOJYiHLmOsXcwGkMDDM
dVtWL4oeBmnKy+/E+gMMXD/LsC4sUeOvGPaLm6PEGloCyCVaV743DOYhA35y2jLWQpj3Q2J6FPuA
BgLGh/mvJwTdXFz8+6tLSz90qtWN+fn52uOPP74PmiLackm5+GQNYDCuIksAGp/IacjZKZYBuHZk
C94gOkZPi2XEAtAk9Ku0/3/ou7sP0w14qBYAFooWrMKRf+6l1sG/Bt38yzDxaevS5/ZpUbFYkJjw
+9v02e7JkycxO9D/yle+EgHbPPfcc+6tW7fIutts0LEzdc/LXe31Xi+47tRirfZll7Ucfpe0ABOv
UyiERKeZGNoNsQNHMwgHxiLT0xzgac7w44CVthBC8AkcJwTX5swDM1xgnqpwdNlAay1HM1JKm7ds
0nLBEO9ZAHGVouLfFHECziSwRnSAh0dukNdpJ1b0cauvjOBzJkCJkmZzj+OPdCDR1UVLGd2nn+IM
gFljwKk+2TUocRI50i/MeymYlSie4ko/VzO/K4A+AiEARbO+Htz7YVhnEnWMbs/Nff/q/Pzrvenp
1Wq5vEOMCu3fA03hmC+//LJPmhtCYLS7u9vb2NiwdSY3pa0AW1uscAMug46JnqcZ0o6tgGw2W3Gc
h98g+FAFAC3Gxt/93d/9Opnv/yct1Mu0SD4tFqKoqK76Hi3oOrQ8LWqH9g36u4Y9av+RCcC89I8+
+sj70z/9U19k04LHs88+O2y1Wm26uXt03OzO/PyFS8NhOd3vl2ZbrZfYhwShouY7QJRZXFQWCQG4
ACmtqXB3XQYDiYZ+WPG+ci7tlY0n7BJoBrQExh8YIAj+2YwMbKk+EeAOEeP1dlvd6nRVA0LQ9wK4
snli0pVsVh0BYpEWSBz044o2WwoerfVt4b4ElgzPQ1RxSDAlUpBm96ME4bBlB6PYs3CAYKWbotbp
3G/RtWwDyyGoUbDVFK6hkFfHSQPOoTDGGTfycM5/XKHoj818AeQhszKeLPNVxnxExnuAttdCYaSb
gALcSEz2AbQ34kys/Wn9d0ulH12anX21trDwcSmf3yLl0jh9+nQHtKTEiITf+Z3fUd/85jfhasL2
t0CvUPsoU9dKDZgVfR0L+B69/0tIDxIdwtK16HtvXbp06f8A/X+aBQBaJ/fJV/+QGPU9ModeJnOo
RYv0Z7Rom0QIV6D10+k0ynxh/jdh/kMA0I0OmB/z0vVIcku4tYEigCtw9uzZER27RaZaam1tLXNr
fv697GhUyrhuqdzrnQmIS7sDans7ZNq5uQBCaiQq01CR5+q954thH1LDG/UCsmYgVl0nSnUD154O
1SDt8OParnp7t6Ya/YHi+Vi+3l9qtTEQV50gzfFSpaqO53MBrLWlCdzRgb8oJmF2B0orQMKDiXOT
49H9hO6/GBSXLuOVEXyUYV7v9tSPmntqFV1wPAVJY/Pf7HXVeTK3p7IZ9eLMrHp+dkbN5HJRl6RS
AiVI9iVIyC7RqGSJ/H4Mx0+P/Gb/39NAMQFaFATSzo7q0r0GvNdImP37+fyFKwsLrwY0Qn7/3Nxc
/cyZMy3QEEx/FZ/w43/729/2v/vd71qaDrtBDAYxo7BeBcxfpL+zRNN/TZ/5mOh6kZ7/CprYyBV4
D3QP+v9UZwHIr7I+/vjjVKlUOqlzsj+mG/r/QeuDKGghB7T1tAXQRi8ALSBqAJANGL333nu6OC+o
wLKMxfTIbIPk7kDqooV4iwzea4uLP8oMh/nTW1uF4nB4NFbrT5ohiLZDCJB57PKMel2a6uo6AY81
IwecjMpBWUocWQU6mxA11GiTdrvbV6+sb6jz9briybi+0ZijxwGoK2QZbJDW+vLsrDpXIF8S56WZ
39ba0jMYloN5nGGI6uFFcFBiBUT9+0Y1oIzyR63Lem169OUPyY34PjovXU8LDx7KoS9AC4I9YrpX
aJ13iBm/cuSIWkIthrRAcI5iUCcHTC2jF8KXEp9HkIk8v8sRfx30A7MPwPxbW0GTT5TyA9x3JnPr
Cpn+q0tLb+XK5U3y+3fOnTu39/TTT3c1DZkDkwKM/69//ev+d77znRHPnNCApUhVd4luC/R6DvEq
2l+n9yEQztDfXwS9o3AI9P+jH/3o0ysA6vW6Rb5QmXyio4iqkpn015lMZgs0TQvkgvnp/a4QAn1a
yOH09LT76quvGijWkRCIBbnhu+3v73dpq5PkTe37furykSM/TFlW5tTGxn+Tc91FJsAgMEjaIbjL
GD9GGoozAbFKOF2k4ySAakQmOEereTIuo/no0d44Vp200A+IGd5vNA6IzgdjhaOmHfwJE/uVnZpK
z9vqyWIhxCoUEXBbWxhBeTO7LUJrynFegdmdSQW/IzV/lC60J6fxSFcAawEX6hKZ1Tinvu/poR3j
UV3jwSrhPzx1GdeMdf3qyoqaIcsmcmMY9owtGrGG5kBSfs6+vqd7LKKxcVogjBBX2tsLMP3xnE1+
aP5uKrV1dXHxby8vLb2RKpfXK5UKTP86mf1d9vtlfJSZn5+fP3/e/8IXvuASLfeJRj0UqtF9AJ2i
3p88NjunO1hRGPTXRMtfIJo+CroH/X+aXQA0ADlk+pdpmyITaQemEi0MKv/gTPWQ4kPhDzZYA2z2
g/l9fxLoXgsBZcYDUCNAbkCHbsDuhQsXUi0SAh973uvEyOlTm5tfJTUxFzOJSZMFDIXOQQTKZBmq
TvEFKTiBPGMJ7c+xgmgcGdcPcK5am6vvkda/SGaxuIJx+4HSs4Z9KxojbmnpAEZ7iwh6PpdVS2Z1
noQUE1qcS4WVmDnIvr0EC/VE+k/iC5g1ARzdr9E64FwC5rfGk3mUFbcAYuPW9QPXDgvgywzTzXUL
3ADF2p4XRVtQMX9fMr9I87EAgKYf4vx2d1Vfm/0DzfwDy9q5Oj//tx8vLLyuqtU10sxbjz32WP2Z
Z54J6kpUfDRisGomvv+3vvUtnzaPvgPag/lPxh0iPGqgC9jypPkxJswGfdN7O6B30L0VYJ3Hh4d+
agTAyy+/bG1vb5O7nZkCXBIx5z/RYtXA6AD5gMaHKQXmp48P6ea45M772ue/Y3zBjAfgsbm5iTru
2tramtN0XftyKvU6aczUY1tb/4ZUwkz07XZ7jB9YqQSVe0HBjE7T+aLN1TdLZqNKu5BgY6O+WCDQ
ViMT+BIxQC+xjNcUBGJCl54juN7vkc/dVbN0fmkOLLLLYebVOc2oLQArYUiIbKO1pVAzav1lFR9J
Y3W91QrOhUFSI61/G8bnB64da/A0ZjJgxDqXWwtTP0iLspASfRAc6OMJ0K5wAdjkh5ZHWy+Yf4Da
EmZ+gH1a1u7VhYXvXT527HW3ULg5VS5vrKys1OD3I+iX5PcfRGwQAnj/z//8z9H2O2g0GkhLo0YY
m4eUNj3SyPkTnX9A730WdA+3lPhgpEeIfboEAJnx1vr6emZubm4Z1VRkDv0XWhQE+Xow9Ynxe8z8
WMh//Md/TNT6B1gBE/EArg9ADwEJGefKlSt2hyQwEcBrRPD2SbIErNGoMpA9+kQ4QQkvMRmIKq2j
6o7IeVuhuRJYBLHov+zi88dzAfixToyzNxhM5OHjuP2WmF0hrQE/EAK3iKifLJVUVnQIBr4++/1c
88+CSfyOndVTdZVG6zX7G5jhRXWgbQgCuCM4h/h0Xqn1rUQhIx9YA6yFFACKBS1fPMN1YwOiE3Mm
p/50sI/9/SGeo++DmD/YoPkhDDSmP2mY5uri4vcuHz36Wq9YvF4sFDaPHTu2+8QTT+x/8YtfHB45
csQ9yO+/He398i//sgf0XxIgPs4D8wGQJQjcMdfNIh4AOj9+/PgXydVY3tnZyRAfPNShIQ9LAARU
gKaKmZmZM+T/r5F/Dqz/pkb4AdMPIEWh+X/wgx/cFfPfSQjogA5uShP92jdv3nTa9LkLKyuBmiYh
8PPZ0ag64C8S4XDePVsuBzlzRw8ZUToY6Igou63LeaNIdYRXP54zz0y2i8Kn4TC+IDKWYOAPRErI
H8cKdlE+LaP+CRpbjsT2hXkfHTdlRy6AZU4YNqG+jRJfaPDd4Bqs8XRjYQXEA5mTo8bwwBpgLSxR
qx9lM3SwlNctauEVpj9r/qEI+oH5+6juo21Axx5qeLgAMp7u/bXFxb+he/5ap1hcLRWLG8vLy7XT
p083X3jhBTD/6CdhfsMlUF/60pdgsSJLMAjbA2wfG+gc9A66JwUI12BfGnmfCgEA8x8BEFoQEr6F
Y2SWg8OR8+9q83+IYF+xWBzRe/fE/HcICkZCAGXEpBUsNA8FQmB5Gd+wT5A7QEKgElkB3D9OxAM0
IY+EQBqVZNyGa2Dy+YyAo4tWZK2/zFkPQaiiVNcX2QQJTxYLCKrQEuDFGIqyV64k9AxgD8uyJir9
fOmrq+SBwTH4b/G3La7P0+egYoczW42Smd8SlYpDreEjJCZYXaafb1T1RXP7ON2H47Dmh88POHj4
/2B+He0H868uLPwt3et/bBeL14j4wPzb586dA/P3RMT/wKDf3QqB//Sf/pNPymuE3D/RM7JQiGsh
PrAOegfdg/6JD3bADw/LDXhoLgBJQgiAdDabnbt69er/Rfttrf2J31yU/gbM/84773g/sZkxGRS0
tRCAlO9E5vj6utUiIfDxygqYwzuxufmvcyImEByBtAksgTQARdBKzDUCYAR092nN6eiOQlv7rRGE
N4OLakEBvx3fGckqt8kLSBjqKUZco2BJmP2x8VwGJr4EAo2KJnTprWTOGC6A+K7ZK2Dr387YEUB6
sq+fcF3SwnH0Wkisfk/0WzDASVTqzBV9+CwYm31+CGVoe2L8QacTofkw8/dsexdmP5i/pZl/aWkp
YH5iwI6mCaa1A4N+d/v42te+5v3FX/xFgF2B84DliCAh6JyUzn988sknfwf0Dz4o6FTop0oA0EX7
u7u7QzRM7O3tXSRpua8XawTmR/DkkzD/HYSASzdcsRCgc4AlYLXo+cfLy2BslyyBr+SGwwVlNOQE
o6GKReWn00HPgM/+v87BR2ksjdLjGWWtHH2fIUuigAIajh1IYE6DaeTcPmkMzWeyqphKxTS0JZg4
9rtKTPWRfQx+3DLwjQIheSwJtY0HfhvnsN0fJJ77BOsnGHJYA6yFEl2OsrgnNrkHKT0O9gm/39WN
PP12O0jzDUWaD1svnd4izf/KhaWlNwLNXyyuk6m/Rb76nmB+934xPz9+8Rd/0UNgkJg/EAKp8IHi
t4uge2S1wAefyjQgJB8APWlhztN+V2P6ocli1G637zbaf1+EAAqF8CRwB2j/0crKiEi6//jOzpeL
/f4JaQ96WvNkSGoDUyDN2l93yY10PT63E0fpLfbL8T4R7hGyIqr0/q5R0noQoyhTe9N2lARR0dZN
M76+KNMFSF6PWL2BlTBP0AzaWQL4xNKZCPw2zuHD/X11YKz/oGvRDI41wFoEuPwSrpvjLJza08LX
012Pno74Bxoeef5wbFwIB6+bfsD87Wx2FUU+V1ZW3urmcjfB/AsLC9sPmvllYPA73/kOgt5D0DXR
OYBsdzXd9z6VFgD5O97c3JxDi18mafhXuuR3RIvjYZG4wu8+Fx3cTghEKK1bW1t+hz77wZEjwyEJ
pcc3N79QbbfPcaFNSnTopeGrIjDIwUFIeU5TMfKswMrj4hkQ8QwJi9PkTmygSYTRiG9jMvsGMy0T
0TwGmCnOAATWha4V8CerE2MxADUePnpQDCBmAegPRcfWx8Rv4xxwLmsImPI5HiB4pEDAWuZpLbAG
WAuG6Iqm9Eh/X+D3wQJwQ6st8PcB3zXUKb6RngkRdPvRtlcsfnhlcfHVi7OzbxOXrZe02f/TYn5+
fP3rX4cQsBHTGgwGtrYC/uqZZ54pk6Lb2tnZ8T5VAiAgnkwGDFlbXV1t53K5IW0efP4Hwfx3KwTg
dgDSaW1tzev4vvuRZY16jtM+tb3dmWs0Xk7LQRO8J8JLIzUFLQbNqtF+ODDoaGbjkeA2YwXQ9my5
rDaIcd7d2xuX/8pRVgcIATQIfXZmRs0D25AbYwRIRlQ0ZG7Kip77PKEX9Q1JnxVbBB8uztHSXX44
B5zLX6+vqz5jEN5B6/Pz02Q9YA0sXb3nC7Pe54o+mebjbj7s4e+jbRyBPj3UY6RBPhAM3JmaeuvS
/Pw/rM7MvG/n85t52oj5a+R7N4j5uz8t5jeFAGDrstlsh+j+0unTp4vcxv7PVgD89m//9k/0PWIy
l7adF154AVyp7jbP/wCFQPAisN7IlHRJKo/ILHCvZTLDbjrdPZVK1Zd3d7+APgKfC1MYXIK2FDat
yTwdHHT0fHpLQ3wztDdPxanS9kViHjDweRICKqkPwAgGFug3fm5hQZ0jxskKhCIpKGI5JVk+e5eP
pO+aIT5ugkINAs4Frs/fbW2pjoZHNwOYMQuG9s9Uq8G1Yw0Ye5/LeD3NyL5E8NHFPjz5aaSZn4d2
jMbVfd21ublXLy8u/nBzZuYCCbmdQqj5d44dO9b83Oc+1zei/Q+c+aUQQJ3A888/jwyB+73vfa97
P3jpE/HDQTyXGJV+wI+flP9/knPVKcIIj4P3ZJKlX3311czHH39c3tzcnO12uwv9fn9+utM5+cTW
1vMnd3d/NtfvL6d1QRCYPqX9/7QecIk+e0en5lIa8MIRjG8bo67rRLjvNpvqbRICDa4NMKba4niP
k8b8zOysOkkmd45dDM0sHmtBHRAb6jFXUSoM/jHy5VxgA6j0fF79XKWi/ubKlfAa6JzQZYhrIpcs
2HAtaaQ+aY8GqZS+vmgasrZu0PZ7jfzwH9Zq6kq7PZ42ZOyn6LsvEvM/R787HUbGx0g9Aq3H1VN6
RiLq70ofX7/HGH7Q+r1sdu3azMxrZPa/s5vPryLiTpp/a3l5eefUqVOtL3zhC4OHxfxGmvCR4a1H
aTTYT1fyHZwiHGLKKxGO/+GHHwJk1CV/zd2zbfd8Ot1uZ7MNEgIvz+7tvRihziAlxpYAEWNKWwFI
FQbWAN4Dw8A1wJ5x/jTzQAt+fmoqMIlvkD+L6jp0zeGk8sRki+ReHKP3ljFhBgzK6TExGSg2IowL
aUQOnQOY/Dmu9Y9iAKKsVonvRSk74/hRW7OudyjQ/gz588vkEiAecIOEwCYAV4BQhGAfMf4KvXeM
tjkIEk7tSabn0dzib1+n+KSWd3mvswF4XqtW3ybmf+vq3NwHg2x2I5fJbFUqlW3S+jVi/jb5/YP7
ner7l/D41AqA2wkB1GcvLi76xWIR+G/upUuXRiQEBn3LGn0wP99uFgq7j6XTO8v1+mfyrjvlasZJ
C7jpNJhfa3rG7/Ml82sBwHtoYDT2LJA5/QJMar5BaIuGpcFpPp4kJJGBzfSZ3IvsRUwjCHfD3MvP
Jh0z6jmQY7dxDWB02lfIQjlFwmqog3ZMaMEcLYY850IeIQCY6Ufc0CNeGwrBwMfFMbqW1SCT/4dX
FxffvlksXk7ncrtg/pmZme3HHnssAPT4/Oc/PxC1/YfM/y9NAHzC0IF0u6M5Hegd+MxnPtMnMxKz
BjwAQZI10Cch0LuVSvU7xeLe/tbW5ont7X9VabefVBqKCwye0s/TGrUX1kE0vEPj+tnaGrD1e2a/
fVaOvTL6+GObQAo2BYIS1XOWMeD0TovBlXexOghxfE9UAzJuokwnwkpxtAvDJbwmqrFrmP6M0++y
xtcWwpB9fxYC+r1msfjR6vz8m9cXFj6sp1K3yAXbpfu1Rf5+nRh/jwQAIv1o7OGOPpns+NQz/20F
wIOMxz2M+MI9CIGISE6ePOlje+WVV9DcAd+xX6vVBr1er1+nrb283NzL5XZO1mrrS7u7P5MdjYqe
Zn4wQAAgAuKGBteWQDCCLESOiQSBp+MB7DJwWW9sEKdYN8n80Sa0ajT2moFFEyYIR1NyJEZggoDx
DHBSm39LfyeG/CvOL7IM5Pd1IJThuSYYX5j+I8nwGtLL1b/dt+32xvz8G9dmZ3+8NjNzaaBULQfN
n8ttk+VWA4Lv888/P/jKV74iwTxkdumRZP6fQgz80AW4m+C36RIQIQ3IpPSnp6cxd2BIWx8gIwN6
rM7OdvYKhdpePr9xrFZ7EdYAT/RJCUy+wJdF7YBmeCZ8R1cSBnUEIn1oGw09E0JTMqgwl32RUlOi
bTbm4x/QDizNfE/AkEsh44m6fk8DkDDu4QQxG1aKHMPtSjNfnP9Q/86IBYNeNxae0Po3Zmffvka+
Pq37rXQ63SiROzY1NbVDmn4P2P3o+tTBPt9g/ntq7Dl0AT6dQkAW27EQ8EFQlUrFfffdd10UdNy4
cWO4tbXV7dBj1/N6zSNH9naLxc3j9fr1pUbjhWyvt+AzqrAOAtoa3srWwcIASFO7ADwF2BHDM+wE
7WqJcmDfaIqREFiu6I1nLeyKIB+n2SINrTvv8BlHMK2rzXtbMySfx0iAjh50bjEXRcRHJGIPuwAj
id8nAn+eFgD9XG5rY2rqnevT0x/crFSujGy7lkunMRS2duTIkcYyWWNnzpwJILzIavOS/P1D5j8U
AD+pEAj27BKgTPnVV19F8VJ3fX291263UU7cu1qttneKxY2jxeK1o/X6M3N7ey/kXLfgCTBRjxle
CAJXM74UBJElIAaWxkp2DVPdNXxpWVHnSY2uOwgjQE3tArh68Ens8zxEU+Mh8vARX2Pyy1iAeV5K
qYnOPV9o8ijCL2v6DW2P93u23dmZmXnn5vT0edqu7KdS29D6xWx2p1wu18jk36N70tYpvsRW3kPm
PxQAn9QdYGKKioa0NTA6f/78cG1tbbCzs9MFDHnbtrsfzM01tiuVtWP1+pWVRuOZ6UYDCBGOpRuG
bJ02dBjEU8cDHK4eFPP1pAVgJ2hazzCxR+xDi4YZJdKGjJzr69l4Kpy+HDYuiT3PEHAZqJOblkTu
PsI7SDonaQGI3n0J1+XLVJ7B+GRhuPWpqfduTU2dvzE9fWknm10HjkPaceqlUmmXGL9x7NixvTto
/cNg36EAeDBxAVgCeJEEQfvtt98GdkFnc3OzU6/XMRFmdlupTn1xcWerXL5xtFS6vNBonJtutZ6K
IMGZ2XWg0NWMLwWAI10BOSQjwQpwZX+8tAY0c0XVdEolluqyo8wYBSMxWpwHlrBpb4tzm9D+ZnxC
wnXJ/n3DTZGQXsThH2xNTX1IGv/CBvn5JKb2Muk0wGJqs7Oz9fn5+ebS0lLnxRdfHGAwDG2uzGIe
av1DAfCgXQI8bE18EAYjsgaGFy5cGFy+fLkNIUAuAabBTK+VSp3NfH5jeXr62sLOzsdHms0np9vt
cywIXF0yzFOIWCiwdpUAHEpYAfIhGS1mCQhm80VGgEFJI/tYa/yY1hZmv0pgfo8nCJvnYgQSPWkB
CHfAFUAeEeMXix+uVyofbc3NXV7L52+4jrOP2ZDFXK6ezWbr09PTe0888UTnbrT+IfMfCoAHZQmo
28UGXn/9dQyQ7NEGi2B/OBzuEyNNXy8W22vZ7K31ubmLy43GBwv7+6eqzeaZjOflA4YVDM/jwPg5
a2LHQOiJBQMZvUj42FHtPAsGreE9zfQorfX7/bDPXgf/LAbbEJgBnDZ09Gdc7SokBf8Y5ceX+Pwi
oCgFAvao3d+rVi+QpXRpbWrq8mY2uzFKpTAEppkic5/8fTKkFptHjhzZp637uc99bnTo6x8KgEc6
NnDt2jX3ww8/7NO+vbOzg0nF+2QNTI0sq3qLiHs9l1ubm5r6aHl//+TS/v4TU7RlBoN5xhccaavA
1hqfmW0k3QAVovd6hhDwROTcNLvZPPck1LbmJIfThILxXaHVueTZlRaJeQ6GW+KJzRUWCJ4PMpnt
Rrl8eYO2tXL5Wi2f36JjB8Nf0qnUXi6Xa1Sr1cbc3Nw+CdfuuXPnhmxxHfr6hwLgUYwNBA/tErBb
MHr//fdhEQCOfI9cg+poNAoEwUY+39wqFDamZ2YuLO7tHV1ot09ON5sny+32Y8RUKU/42I40/Q9y
A0Sen7Wsa2DmsQVgMyMClZgZVoWpPUczcTR1V4UlvCP9PVvHBm53DvzcNWMUvj/aLxav1iuVa1vF
4rXNavUmqfhdeh2j39pgfGj8qampZrlcbqGSj0z+4aG5fygA/jm5BSwI4BZ48/Pzo+3t7QEJAqQM
WxAEtVqtTK4BgEerNd9v7szMbK7Ozl6a7Xbn55vNlZn9/aPTnc6JfLd7nKf5SMz+JLwAWenH2lZC
abEJju+6xgVwANBmkFGOT2irIRp7xZgDSYVJ0rowXIFuPn+9Xiis7pbLN7crlVuk7bdbvr9Hx+iS
md8i8wmM35ydnd0H48PUf/rppweC8c2CnkPGPxQAj6w1oES2wP/85z8fpNmlIKA9EGGajUajToKg
3O/3Kx0SBPvZ7O6NxcXrpbm58lyrtUDbyky3u1zqdJYLvd4KMWjaMhB2k4QAg2dGwzSkXy7cBV8X
8vCkXV+a/rq2nwMdjk4LHsT8sR4Cyxp2crlbrUJhbTefX9splW7RttVynH36rQ4JsQ4dr5XNZjGj
YZ80fpvM/RatUQ+Mj7WidXMN//7Q3D8UAP8s3YKYIIBWI9dg8MEHH3TIGshtbGw0ut1uqdlslkgQ
lOlDRVKNxb1yefsq+celwaA8MxjMVtvt+alud6FMG31wOdPvL04EI4wqPE8yu0jNKY1XyIVAQS+C
GDNuicBGUAUorIDIAjAueJDNbhJHr+2TL9+gba9Y3N7NZGqtTGaffrFHH+nZIeoSvZRpVSqVVj6f
by0tLXVJ6/eeeuqpUYLGPzT3DwXAvxi3IAAgYdcAxH7t2jWkDjsXL15sERPkBoNBgayCIgkCCIOC
T4Kgmck0GqnUllUsXnYGg/yM51WLbVKY3e5sudebLQyHs/l+fyZLLgX559MYdcbmt5JBORHM40Ig
HlvG1YHsAvCwUXY9oIo5A0GvjVzbrg/IZO+SxdJJp2v7uRx6IWrtYnFv17b33EymS78TzMaDmU/H
agMGi7YWtD0JgA4JgN7p06f7Z86ccUVwbwLE7JDxH+zDehgdSAd1Az6Mc3nQl2rsI0HAz0kIOJhL
cOXKlfSlS5dSJASya2trWRIAxOftPDbS2oXRaJSnz+f0lnZdN50aDjO54bBQoi3f65UKg0El77ol
EgZFZzjM5YfDmQwJjJTrlulGkwvv2xhIOfK8oZNKZUhgFAMTJYTlGpE70MNwFBIQfdpGQzLZh8TQ
HQTq0ul+P51ud8ln72QyzW4u12ql050ebaN0GtNv0HyDLdD2mOtIx+0Ui8UuNgx9XV5e7gP9+cUX
XxzCzCdf3zeKeBIZXz3E4Zn/0un/kRIA/2LNgvGEIvPCbfk6hMH58+dtEgBpep7CPLmtra0MXIXh
cJjvdDpZ7CEkMHGWjouBeikSECniX4DPOzYYfTBwiPHTXr9vZ30/gz2Z+HDi7Y7r9uvEoDsj4J06
eoapq+ZSqdwUCZei42CgnUcugmdnsx6p8AH2pM6HVibjkgXgEnMHG+Y40NdHdD/7epozpjh3C4VC
sIdpv7CwAOHQh5YnATB85plnPM306gAzP3rdsiz/U0YnhwLgUyIMrARLITachwSADWGwt7eXgmWw
sbGRIgFAarhPqreVoecZep6BkKA9GQNDCIU0hAH9BoSBRYICI6lset3B8BN33C3ou2HrsR3G+zzM
rbOChiTH8cUejO4BuZb2PqY2genpOSY3kdufHYG5aT8gph9gMi4979HzIfn2o1OnTo2q1epIM/0E
IEeCZvc/bUx/KAA+3YJA3YUwUCQA7O3tbRt7chfsRqORwWh1EgQOuQipbreLDcIh3ev1wPCwHhwI
BhICEA6B+U9/BweFtQ/rA0ICv+GEyMUB4+PUcrkc/nZJiwdjrjWju5hwA/h2+nuYz+exjdAaDYRb
mPTk3w/IrPeI8ZH+DPYJprx/qO0PBcBh9OXehUH0/gcffGCtrq5aH330EZjdvn79ukNuAqwFB0NX
MXyCmN0B45OQsMlasPEbJByiY9BnPXl80tTR7E4tADzS5B4xtwdBQEwPYYDJTT591gW+/fHjxyEU
vCeffNI7ceKE/9RTTyX57IdMfygADgXAfRAGtwssYtoSAoksIFStVsO8QxuvkSCA+R+8t7Oz429u
biaOHyCtbZHPHjyHC0CM7z/++OM+mfPe7OwsGDx4D6+9/PLLiUx9m4DdIdM/ggLg/xdgAJ/G1v7z
h5WQAAAAAElFTkSuQmCC"""

        if os.getenv('DEBUG_EXTRA'):
            print("make_icon -> imgfile =", imgfile)
            print("make_icon -> type(stricon) =", type(stricon))
            print("make_icon -> len(stricon) =", len(stricon))

        if sys.version_info.major == 2:
            with open(imgfile, 'wb') as img:
                img.write(stricon.decode('base64'))
        else:
            try:
                with open(imgfile, 'wb') as img:
                    import base64
                    img.write(base64.b64decode(stricon))
            except TypeError:
                with open(imgfile, 'w') as img:
                    import base64
                    img.write(base64.b64decode(stricon))            
                    
        if os.getenv('DEBUG_EXTRA'): print("make_icon -> imgfile =", imgfile)
        
        return imgfile
    
    @classmethod
    def growl(cls, app, name = 'info', title = 'xnotify', message = '', event = [], host = None, timeout = None, icon = None, gntp_callback = None, callback = None, sticky = False, priority = None, **kwargs):
        #os.environ.update({'DEBUG': '1',})
        title = title or cls.title or cls.conf.get_config('growl', 'title')
        app = app or cls.app or cls.conf.get_config('growl', 'app')
        debug(app = app) 
        message = message or cls.message
        event = event or cls.event or cls.conf.get_config('growl', 'event')
        host = host or cls.host or cls.conf.get_config('growl', 'host') or ['127.0.0.1']
        #port = port or cls.port or cls.conf.get_config('growl', 'port') or 23053
        sticky = sticky or cls.sticky or cls.conf.get_config('growl', 'sticky') or False
        priority = priority or cls.priority or cls.conf.get_config('growl', 'priority') or None
        timeout = timeout or cls.timeout or cls.conf.get_config('growl', 'timeout')
        icon = icon or cls.icon or notify.icon or cls.conf.get_config('growl', 'icon')
        debug(icon = icon)
        if icon and not isinstance(icon, Resource):
            if not os.path.isfile(icon):
                try:
                    icon = Resource(icon)
                except:
                    ctraceback.CTraceback(*sys.exc_info())
                    if os.getenv('TRACEBACK') == '1':
                        print(make_colors(traceback.format_exc(), 'lw', 'r'))
            debug(icon = icon)
        elif icon and isinstance(icon, Resource):
            pass
        # else:   
        #     icon = cls.makeicon()
        #     debug(icon = icon)

        debug(icon = icon)
        debug(host = host)
        debug(event = event)

        if not event and name:
            event = [name]
        if event and not isinstance(event, list): event = [event]
        if name and event and isinstance(event, list) and not name in event:
            event.append(name)

        HOSTS = []

        debug(host_1 = host)
        if host and isinstance(host, str):
            host = list(filter(None, [i.split()[0] for i in re.split(",|\n", host)]))
            debug(host_2 = host)
        if host and isinstance(host, bytes):
            host = list(filter(None, [i.split()[0] for i in re.split(",|\n", host.decode('utf-8'))]))
            debug(host_3 = host)  
        if host and isinstance(host, list):
            for h in host:
                if ":" in h:
                    ho, po = h.split(":")
                    ho = ho.strip()
                    po = po.strip()
                    if po and po.isdigit() and ho:
                        HOSTS.append({'host': ho, 'port': int(po),})
                    elif ho:
                        HOSTS.append({'host': ho, 'port': 23053,})
                else:
                    HOSTS.append({'host': h, 'port': 23053,})


        debug(is_growl_active = cls.conf.get_config('service', 'growl'))

        debug(HOSTS = HOSTS)
        debug(event = event)
        
        if not name and isinstance(event, list):
            name = event[0]

        if cls.conf.get_config('service', 'growl', 0) == 1 or cls.conf.get_config('service', 'growl', 0) == "1" or os.getenv('XNOTIFY_GROWL') == '1' or os.getenv('GROWL') == '1' or os.getenv('NOTIFY_GROWL') == '1'or cls.active_growl:

            #growl = sendgrowl.Growl(app, EVENT, icon)
            error = False
            debug(app = app)
            debug(event = event)
            debug(title = title)
            debug(message = message)
            debug(icon = icon)
            debug(name = name)
            debug(timeout = timeout)
            debug(gntp_callback = gntp_callback)
            #debug(growl_file = sendgrowl.__file__)

            for HOST in HOSTS:
                debug(HOST = HOST)
                try:
                    debug(event = event)
                    debug(icon = icon)
                    publisher = Publisher(app, event, host = HOST['host'], port = HOST['port'], icon = icon or cls.makeicon(), timeout = timeout)
                    publisher.publish(name, title, message, None, sticky, priority, icon, None, callback, gntp_callback, **kwargs)
                except:
                    try:
                        debug(event = event)
                        debug(icon = icon)
                        publisher = Publisher(app, event, host = HOST['host'], port = HOST['port'], icon = icon or cls.makeicon(), timeout = timeout)
                        publisher.register()
                        publisher.publish(name, title, message, None, sticky, priority, icon, None, callback, gntp_callback, **kwargs)
                    except:
                        ctraceback.CTraceback(*sys.exc_info())
                        if os.getenv('TRACEBACK'): print(traceback.format_exc())
                        print(make_colors("ERROR:", 'lw', 'r'), f"{make_colors('Cant send', 'lw', 'bl')} {make_colors('notify', 'b', 'ly')} {make_colors('to GROWL !', 'b', 'lg')} {make_colors(HOST, 'lw', 'm')}")
                        error = True
            if error:
                return False    
            return True
        else:
            print(make_colors("[GROWL]", 'lightwhite', 'lightred') + " " + make_colors('warning: Growl is set True but not active, please change config file to true or 1 or set GROWL=1 to activate !', 'lightred', 'lightyellow'))
            #os.environ.pop('DEBUG')
        return False            

    @classmethod
    def pushbullet(cls, title = None, message = None, api = None, debugx = False):
        if debugx: os.environ.update({'DEBUG': '1',})
        api = api or cls.pushbullet_api or cls.conf.get_config('pushbullet', 'api')
        title = title or cls.title or cls.conf.get_config('pushbullet', 'title')
        message = message or cls.message or cls.conf.get_config('pushbullet', 'message')
        if not api:
            if os.getenv('DEBUG') == '1':
                print(make_colors("[Pushbullet]", 'lightwhite', 'lightred') + " " + make_colors('API not Found', 'lightred', 'lightwhite'))
            return False
        debug(cls_active_pushbullet = cls.active_pushbullet)
        debug(cls_conf_get_config = cls.conf.get_config('service', 'pushbullet', value = 0))
        debug(cls_active_pushbullet = cls.active_pushbullet)
        debug(os_getenv_PUSHBULLET = os.getenv('PUSHBULLET'))

        if cls.active_pushbullet or cls.conf.get_config('service', 'pushbullet', value = 0) == 1 or cls.active_pushbullet or cls.conf.get_config('service', 'pushbullet', value = 0) == "1" or os.getenv('PUSHBULLET') == '1':
            try:
                pb = PB.Pushbullet(api)
                pb.push_note(title, message)
                if os.getenv('DEBUG'): os.environ.pop('DEBUG')
                return True
            except:
                ctraceback.CTraceback(*sys.exc_info())
                cls.logger(str(traceback.format_exc(growl = 0, syslog = 0)), 'error')                
                print("send to pushbullet ERROR !, see log file. '{}'".format(cls.logfile))                
                if os.getenv('DEBUG') == '1':
                    print(make_colors("ERROR [PUSHBULLET]:", 'lightwhite', 'lightred', 'blink'))
                    print(make_colors(traceback.format_exc(), 'lightred', 'lightwhite'))
                if os.getenv('DEBUG') == '1':
                    print(make_colors("[Pushbullet]", 'lightwhite', 'lightred') + " " + make_colors('sending error', 'lightred', 'lightwhite'))
                if os.getenv('DEBUG'): os.environ.pop('DEBUG')
                return False
        #else:
            #print(make_colors("[PUSHBULLET]", 'lightwhite', 'lightred') + " " + make_colors('warning: Pushbullet is set True but not active, please change config file to true or 1 or set TRACEBACK_PUSHBULLET=1 to activate !', 'lightred', 'lightyellow'))
        if os.getenv('DEBUG'): os.environ.pop('DEBUG').s
        return False            

    @classmethod
    def nmd(cls, title = None, message = None, api = None, debugx = True, timeout = 3):
        if os.getenv('DEBUG'): os.environ.update({'DEBUG': '1',})

        import warnings
        warnings.filterwarnings("ignore")
        url = "https://www.notifymydevice.com/push"#?ApiKey={0}&PushTitle={1}&PushText={2}"
        debug(url_nmd = url)
        api = api or cls.nmd_api or cls.conf.get_config('nmd', 'api')
        debug(api = api)
        title = title or cls.title or cls.conf.get_config('nmd', 'title')
        debug(title = title)
        message = message or cls.message or cls.conf.get_config('nmd', 'message')
        debug(message = message)
        if not api:
            print(make_colors("[NMD]", 'lightwhite', 'lightred') + " " + make_colors('API not Found', 'lightred', 'lightwhite'))
            return False
        data = {"ApiKey": api, "PushTitle": title,"PushText": message}
        debug(data = data)
        debug(cls_active_nmd = cls.active_nmd)
        debug(service_nmd_config = cls.conf.get_config('service', 'nmd', value = 0))
        if os.getenv('NMD') == '1': cls.active_nmd = True
        if cls.active_nmd or cls.conf.get_config('service', 'nmd', value = 0) == 1 or cls.conf.get_config('service', 'nmd', value = 0) == "1":
            try:
                a = requests.post(url, data = data, timeout = timeout)
                return a
            except:
                ctraceback.CTraceback(*sys.exc_info())
                try:
                    a = requests.post(url, data = data, timeout = timeout, verify = False)
                    debug(a = a)
                    debug(a_content = a.content)
                    if os.getenv('DEBUG'): os.environ.pop('DEBUG')
                    return a
                except:
                    ctraceback.CTraceback(*sys.exc_info())
                    cls.logger(str(traceback.format_exc(growl = 0, syslog = 0)), 'error')                

                    if os.getenv('DEBUG') == '1' or os.getenv('TRACEBACK') == '1':
                        print("send to NMD ERROR !, see log file. '{}'".format(cls.logfile))
                        print(make_colors("ERROR [NMD]:", 'lightwhite', 'lightred', 'blink'))
                        print(make_colors(traceback.format_exc(), 'lightred', 'lightwhite'))
                    else:
                        traceback.format_exc()
                    if os.getenv('DEBUG') == '1':
                        print(make_colors("[NMD]", 'lightwhite', 'lightred') + " " + make_colors('sending error', 'lightred', 'lightwhite'))
                    if os.getenv('DEBUG'): os.environ.pop('DEBUG')
                    return False
        else:
            if os.getenv('DEBUG') == '1':
                print(make_colors("[NMD]", 'lightwhite', 'lightred') + " " + make_colors('warning: NMD is set True but not active, please change config file to true or 1 or set TRACEBACK_NMD=1 to activate !', 'lightred', 'lightyellow'))
            if os.getenv('DEBUG'): os.environ.pop('DEBUG')
            return False

    @classmethod
    def notify(cls, *args, **kwargs):
        return cls.send(*args, **kwargs)

    @classmethod
    def show_config(cls):
        all_config = cls.conf.read_all_config()
        return all_config

    @classmethod
    def get_config(cls, *args, **kwargs):
        return cls.conf.get_config(*args, **kwargs)

    @classmethod
    def read_config(cls, *args, **kwargs):
        return cls.conf.read_config(*args, **kwargs)

    @classmethod
    def write_config(cls, *args, **kwargs):
        return cls.conf.write_config(*args, **kwargs)

    @classmethod
    def send(cls, app = None, name = None, title = "this is title", message = "this is message", event = None, host = None, port = None, timeout = None, icon = None, pushbullet_api = None, nmd_api = None, growl = True, pushbullet = False, nmd = False, ntfy = True, debugx = False, callback = None, gntp_callback = None, ntfy_servers = None, sticky = False, priority = None, ntfy_icon = '', syslog = True, syslog_server = [], server_host = None, server_port = None, to_server_only = False, message_color = None, syslog_severity = 'info', syslog_facility = 'daemon', **kwargs):
        if debugx: os.environ.update({'DEBUG': '1',})
        
        if isinstance(name, list) and len(name) > 0: name = name[0]

        debug(cls_server_as_router = cls.server_as_router)
        if not cls.server_as_router:
            cls.client(title, (message_color or message))
        if to_server_only:
            return True
        p1 = p2 = p3 = p4 = None
        debug(ntfy_servers = ntfy_servers)
        debug(host = host)
        debug(title = title)
        title = title or cls.title or 'xnotify'
        debug(title = title)
        message = message or cls.message
        debug(cls_app = cls.app)
        app = app or cls.app or 'xnotify'
        debug(app = app)
        debug(event = event)
        debug(cls_event = cls.event)
        if event and cls.event:
            event += cls.event
            event = list(set(event))
            debug(event = event)
        else:
            event = event or cls.event or []
            debug(event = event)
        if isinstance(event, list) and name and not name in event: event.append(name)
        debug(event = event)
        debug(host = host)
        port = port or cls.port or 5432
        timeout = timeout or cls.timeout or 20
        icon = icon or cls.icon
        debug(cls_icon = cls.icon)
        debug(icon = icon)
        pushbullet_api = pushbullet_api or cls.pushbullet_api or cls.conf.get_config('pushbullet', 'api')
        nmd_api = nmd_api or cls.nmd_api or cls.conf.get_config('nmd', 'api')
        sticky = sticky or cls.sticky
        ntfy_icon = ntfy_icon or cls.ntfy_icon
        debug(cls_syslog = cls.syslog)
        syslog = syslog or cls.syslog
        syslog_server = syslog_server or cls.syslog_server
        server_host = server_host or '0.0.0.0'
        server_port = server_port or 33000

        if pushbullet:  
            cls.active_pushbullet = True
        if growl:
            cls.active_growl = True
        if nmd:
            cls.active_nmd = True
        if ntfy:
            cls.active_ntfy = True

        debug(is_ntfy_enable = (ntfy and (cls.conf.get_config('service', 'ntfy', '0') == '1' or cls.conf.get_config('service', 'ntfy', '0') == 1)) or os.getenv('NTFY') == '1')

        if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", "growl:", (growl and (cls.conf.get_config('service', 'growl', '1') == '1' or cls.conf.get_config('service', 'growl', '1') == 1)) or os.getenv('GROWL') == '1')

        if (growl and (cls.conf.get_config('service', 'growl', '1') == '1' or cls.conf.get_config('service', 'growl', '1') == 1)) or os.getenv('GROWL') == '1':
            if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", 'send to growl ...')
            debug(title = title)
            debug(app = app)
            debug(event = event)
            debug(message = message)
            debug(host = host)
            debug(port = port)
            debug(gntp_callback = gntp_callback)
            debug(icon = icon)

            #cls.growl(app, name, title, message, event, host, timeout, icon, gntp_callback, callback, sticky, priority, **kwargs)

            try:
                p1.terminate()
            except:
                pass
            try:
                p1 = Process(target = cls.growl, args = (app, name, title, message, event, host, timeout, icon, gntp_callback, callback, sticky, priority), kwargs = kwargs)
                p1.start()
            except:
                ctraceback.CTraceback(*sys.exc_info())
                cls.logger(traceback.format_exc(growl = 0, syslog = 0), 'error')
                print("error send message to growl ! [see log file !]")
                if os.getenv('TRACEBACK') == '1':
                    print(traceback.format_exc())
                if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", make_colors("growl error:", 'lw', 'r') + " " + make_colors(traceback.format_exc(), 'lw', 'r'))

        if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", "pushbullet:", (pushbullet and (cls.conf.get_config('service', 'pushbullet', '0') == '1' or cls.conf.get_config('service', 'pushbullet', '0') == 1)) or os.getenv('PUSHBULLET') == '1')
        debug(pushbullet = pushbullet)

        if (pushbullet or (cls.conf.get_config('service', 'pushbullet', '0') == '1' or cls.conf.get_config('service', 'pushbullet', '0') == 1)) or os.getenv('PUSHBULLET') == '1':
            if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", "send to pushbullet ...")
            if pushbullet_api or cls.conf.get_config('pushbullet', 'api'):
                cls.pushbullet(title, message, pushbullet_api, debugx)

                #try:
                    #p2 = Process(target = cls.pushbullet, args = (title, message, pushbullet_api, debugx))
                    #p2.start()
                #except:
                    #try:
                        #cls.pushbullet(title, message, pushbullet_api, debugx)
                    #except:
                        #cls.logger(traceback.format_exc(growl = 0, syslog = 0), 'error')
                        #print("error send message to pushbullet ! [see log file !]")

                    #traceback.format_exc()
                if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", make_colors("pushbullet error", 'lw', 'r'))
            else:
                print(make_colors("pushbullet is active but no API !", 'b', 'y'))

        if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", "nmd:", (nmd and (cls.conf.get_config('service', 'nmd', '0') == '1' or cls.conf.get_config('service', 'nmd', '0') == 1)) or os.getenv('NMD') == '1')
        if (nmd and (cls.conf.get_config('service', 'nmd', '0') == '1' or cls.conf.get_config('service', 'nmd', '0') == 1)) or os.getenv('NMD') == '1':
            if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", "send to nmd ...")
            if nmd_api or cls.conf.get_config('nmd', 'api'):
                #cls.nmd(title, message, nmd_api, debugx = debugx)

                try:
                    p3 = Process(target = cls.nmd, args = (title, message, nmd_api, debugx))
                    p3.start()
                except:
                    try:
                        cls.nmd(title, message, nmd_api, debugx)
                    except:
                        cls.logger(traceback.format_exc(growl = 0, syslog = 0), 'error')
                        print("error send message to nmd ! [see log file !]")

                    traceback.format_exc()
                if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", make_colors("nmd error", 'lw', 'r'))

            else:
                print(make_colors("NMD is active but no API !", 'b', 'y'))
        debug(ntfy = ntfy)

        if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", "ntfy:", (ntfy and (cls.conf.get_config('service', 'ntfy', '0') == '1' or cls.conf.get_config('service', 'ntfy', '0') == 1)) or os.getenv('NTFY') == '1')
        if (ntfy and (cls.conf.get_config('service', 'ntfy', '0') == '1' or cls.conf.get_config('service', 'ntfy', '0') == 1)) or os.getenv('NTFY') == '1':
            if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", "send to ntfy ...")
            ntfy_icon = None
            if ntfy_icon or icon:
                try:
                    if 'http' == icon[:4]:
                        ntfy_icon = icon
                except:
                    pass
                    #traceback.format_exc()

            debug(ntfy_servers = ntfy_servers)
            #cls.ntfy(app, title, message, ntfy_icon, server = ntfy_servers)

            try:
                p4 = Process(target = cls.ntfy, args = (app, title, message, ntfy_icon, ntfy_servers))
                p4.start()
            except:
                try:
                    cls.ntfy(app, title, message, ntfy_icon, ntfy_servers)
                except:
                    cls.logger(traceback.format_exc(growl = 0, syslog = 0), 'error')
                    print("error send message to ntfy ! [see log file !]")

                traceback.format_exc()
            if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", make_colors("ntfy error", 'lw', 'r'))

        debug(syslog = syslog)
        if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", "syslog:", syslog)
        if syslog:
            if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", "send to syslog ...")
            syslog_server = syslog_server or ['127.0.0.1']
            for i in syslog_server:
                if ":" in i:
                    host, port = i.split(":")
                else:
                    host = '127.0.0.1'
                    port = 514
                debug(host = host)
                debug(port = port)
                tmessage = title + ": " + message
                #print("TMESSAGE:", tmessage)
                if SYSLOGX:
                    syslogx.syslog(tmessage, syslogx.LEVEL[(syslog_severity or 'info')], syslogx.FACILITY[(syslog_facility or 'daemon')], host.strip(), int(str(port).strip()))
        if os.getenv('DEBUG'):
            os.environ.pop('DEBUG')
        return True

    @classmethod
    def server(cls, host = '0.0.0.0', port = 33000, as_router = False):
        cls.server_as_router = as_router
        sound = ''
        active_sound = False
        if cls.conf.get_config('sound', 'active', '1') == 1:
            active_sound = True
            sound = os.path.join(os.path.dirname(__file__), 'sound.wav')
            if not os.path.isfile(sound):
                sound = cls.conf.get_config('sound', 'file')

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind((host, port))
            print(make_colors("Server Listen On: ", 'lightwhite', 'lightblue') + make_colors(host, 'lightwhite', 'lightred') + ":" + make_colors(str(
                port), 'black', 'lightcyan') + " " + make_colors("PID:", 'lm') + " " + make_colors(str(os.getpid()), 'lw', 'm'))            
            while True:
                try:
                    #s.listen(8096) #TCP
                    #conn, addr = s.accept() #TCP
                    data, addr = s.recvfrom(8096)
                    debug(data = data)
                    if data:
                        #data = conn.recv(8096) #TCP
                        title = ''
                        message = ''
                        if hasattr(data, 'decode'):
                            data = data.decode('utf-8')
                        data_title = re.findall('.*?title:(.*?)message:', data)
                        if data_title:
                            title = data_title[0].strip()
                        data_message = re.findall('.*?message:(.*?)$', data)
                        if data_message:
                            message = data_message[0].strip()
                        date = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S%f')

                        if title and message:
                            print(make_colors(date, 'lightyellow') + " " + make_colors(addr[0] + ":" + str(addr[1]), 'lw', 'm') + " - "+ make_colors("title =>", 'black', 'lightgreen') + " " + make_colors(str(title), 'lightgreen') + " " + make_colors("message =>", 'lightwhite', 'lightblue') + " " + make_colors(message, 'lightblue'))
                            if active_sound and sound:
                                winsound.PlaySound(sound, winsound.SND_ALIAS)
                            debug(as_router = as_router)
                            if as_router:
                                cls.send(title, message)

                        #print("data =", data)
                        #print("title =", title)
                        #print("message =", message)

                except:
                    traceback.format_exc(syslog = '0')
                    sys.exit()
        except:
            traceback.format_exc(syslog = '0')
            sys.exit()

    @classmethod
    def client(cls, title, message, host = '127.0.0.1', port = 33000):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            data = "title: {0} message: {1}".format(title, message)
        except:
            data = "title: {0} message: {1}".format(title.encode('utf-8'), message.encode('utf-8'))
        if sys.version_info.major == 3:
            data = bytes(data.encode('utf-8'))
        s.sendto(data, (host, port))

    def test(cls):
        #def notify(self, title = "this is title", message = "this is message", app = None, event = None, host = None, port = None, timeout = None, icon = None, pushbullet_api = None, nmd_api = None, growl = True, pushbullet = True, nmd = True, debugx = True):
        cls.notify()

    def usage(cls):
        parser = argparse.ArgumentParser(formatter_class = argparse.RawTextHelpFormatter)
        # parser.add_argument('COMMAND', help = 'Command [serve]', nargs='?')
        parser.add_argument('-g', '--growl', action = 'store_true', help = 'Active Growl')
        parser.add_argument('-p', '--pushbullet', action = 'store_true', help = 'Active Pushbullet')
        parser.add_argument('-n', '--nmd', action = 'store_true', help = 'Active NotifyMyAndroid')
        parser.add_argument('-papi', '--pushbullet-api', action = 'store', help = 'Pushbullet API')
        parser.add_argument('-pnmd', '--nmd-api', action = 'store', help = 'NotifyMyAndroid API')
        parser.add_argument('-a', '--app', action = 'store', help = 'App Name for Growl')
        parser.add_argument('-e', '--event', action = 'store', help = 'Event Name for Growl')
        parser.add_argument('-i', '--icon', action = 'store', help = 'Icon Path for Growl')
        parser.add_argument('--growl-host', action = 'store', help = 'Host for Growl and Snarl', nargs = '*')
        parser.add_argument('--growl-port', action = 'store', help = 'Port for Growl and Snarl')
        parser.add_argument('-t', '--timeout', action = 'store', help = 'Timeout for Growl and Snarl')
        parser.add_argument('-x', '--priority', action = 'store', help = 'Priority for Growl and Snarl')
        parser.add_argument('TITLE', action = 'store', help = 'Title of Message', nargs='?')
        parser.add_argument('MESSAGE', action = 'store', help = 'Message', nargs='?')
        parser.add_argument('-s', '--server', action = 'store_true', help = 'start server')
        parser.add_argument('-r', '--server-as-router', action = 'store_true', help = 'start server as router')
        parser.add_argument('-H', '--server-host', action = 'store', help = 'Server/Router Bind/Listen On, default = 0.0.0.0', default = '0.0.0.0')
        parser.add_argument('-P', '--server-port', action = 'store', help = 'Server/Router bind/listen port, default = 33000', default = 33000, type = int)
        parser.add_argument('-c', '--client', action = 'store_true', help = 'start test client')

        parser.add_argument('--ntfy', action = 'store_true', help = 'Active ntfy')
        parser.add_argument('--ntfy-hosts', action = 'store', help = 'ntfy servers', nargs = '*')
        parser.add_argument('--ntfy-icon', action = 'store', help = 'ntfy icon, icon must url')
        parser.add_argument('--ntfy-priority', action = 'store', help = 'ntfy priority', type = int)
        parser.add_argument('--ntfy-tags', action = 'store', help = 'ntfy tags')
        parser.add_argument('--ntfy-click', action = 'store', help = 'ntfy click')
        parser.add_argument('--ntfy-attach', action = 'store', help = 'ntfy attach')
        parser.add_argument('--ntfy-email', action = 'store', help = 'ntfy email')
        parser.add_argument('--ntfy-filename', action = 'store', help = 'ntfy filename')

        parser.add_argument('--no-growl', help = 'Disable send to growl', action = 'store_false')
        parser.add_argument('--no-pushbullet', help = 'Disable send to pushbullet', action = 'store_false')
        parser.add_argument('--no-nmd', help = 'Disable send to nmd', action = 'store_false')
        parser.add_argument('--no-ntfy', help = 'Disable send to ntfy', action = 'store_false')
        parser.add_argument('--no-syslog', help = 'Disable send to syslog', action = 'store_false')

        parser.add_argument('--sticky', help = 'Set growl sticky: message no disappear', action = 'store_true')
        parser.add_argument('-d', '--debug', help = 'Show debugging', action = 'store_true')
        parser.add_argument('--callback', help = 'GNTP Callback growl', action = 'store')
        parser.add_argument('--syslog-server', help = 'Custom syslog servers, default is "localhost" and from config file', action = 'store', nargs = '*')
        parser.add_argument('--syslog-severity', help = 'Syslog severity, default is "info" and from config file', action = 'store', default = "info")
        parser.add_argument('--syslog-facility', help = 'Syslog facility, default is "daemon" and from config file', action = 'store', default = "daemon")
        parser.add_argument('-so', '--to-server-only', help = 'disable/off growl, pushbullet, nmd, ntfy but enable send to server/router', action = 'store_true')


        if len(sys.argv) == 1:
            parser.print_help()
        else:
            if '-s' in sys.argv[1:] or '--server' in sys.argv[1:]:
                cls.server()
            elif '-r' in sys.argv[1:] or '--server-as-router' in sys.argv[1:]:
                cls.server(as_router = True)
            else:
                args = parser.parse_args()

                cls.syslog = args.no_syslog
                cls.active_growl = args.no_growl
                cls.active_nmd = args.no_nmd
                cls.active_pushbullet = args.no_pushbullet
                cls.active_ntfy = args.no_ntfy

                if args.server:
                    cls.server()
                else:
                    if args.to_server_only:
                        cls.syslog = False
                        cls.active_growl = False
                        cls.active_nmd = False
                        cls.active_pushbullet = False
                        cls.active_ntfy = False

                    gntp_callback = None
                    if args.callback:
                        gntp_callback = eval(args.callback)

                    if args.TITLE and args.MESSAGE:
                        if args.growl and not args.to_server_only:
                            #cls.growl(args.TITLE, args.app, args.event, args.MESSAGE, args.growl_host, args.growl_port, args.timeout, args.icon)
                            cls.growl(args.app, args.event, args.TITLE, args.MESSAGE, args.event, args.growl_host, args.timeout, args.icon, sticky = args.sticky)
                        elif args.pushbullet and not args.to_server_only:
                            cls.pushbullet(args.TITLE, args.MESSAGE, args.pushbullet_api)
                        elif args.nmd and not args.to_server_only:
                            cls.nmd(args.TITLE, args.MESSAGE, args.nmd_api)
                        elif args.ntfy and not args.to_server_only:
                            cls.ntfy(args.app, args.TITLE, args.MESSAGE, args.ntfy_icon, args.ntfy_priority, args.ntfy_tags, args.ntfy_click, args.ntfy_attach, None, args.ntfy_email, args.ntfy_filename, server=args.ntfy_hosts)
                        else:
                            debug(args_ntfy_hosts = args.ntfy_hosts)
                            server_host = args.server_host
                            if server_host == '0.0.0.0':
                                server_host = '127.0.0.1'                    
                            if args.server or args.server_as_router:
                                cls.server(args.server_host, args.server_port, args.server_as_router)

                            elif args.client:
                                cls.client(args.TITLE, args.MESSAGE, server_host, args.server_port)
                            else:
                                cls.send(args.app, args.event, args.TITLE, args.MESSAGE, args.event, args.growl_host, args.growl_port, args.timeout, args.icon, args.pushbullet_api, args.nmd_api, args.no_growl, args.no_pushbullet, args.no_nmd, args.no_ntfy, args.debug, gntp_callback, gntp_callback, args.ntfy_hosts, args.sticky, args.priority, args.ntfy_icon, args.no_syslog, args.syslog_server, server_host, args.server_port, args.to_server_only, None, args.syslog_severity)

def usage():
    c = notify('xnotify')
    c.usage()

if __name__ == '__main__':
    #notify.ntfy('battmon', 'test from python', "FULL", "https://www.clipartmax.com/png/small/457-4573861_512-x-512-1-battery-full-icon-png.png")
    #notify.ntfy('battmon', 'test from python', "FULL", "c:\PROJECTS\battmon\icon.png")
    usage()
    #c.server()
    #c.test_client()
    
    #from mpd import MPDClient
    #c = MPDClient()
    #c.connect('127.0.0.1', 6600)
    #song = c.currentsong()
    
    #n = notify('MPD-Ticker', ['New Song'])
    #n.send(title = 'MPD Ticker - New Song', message = f"{song.get('title')}\n{song.get('album')}\n{song.get('artist')}\n", icon = 'growl.png')

# by LICFACE <licface@yahoo.com>

