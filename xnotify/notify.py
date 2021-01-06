#!/usr/bin/env python2
from __future__ import print_function
import sys, os
import argparse
from configset import configset
import pushbullet as PB
import sendgrowl
from pydebugger.debug import debug
from make_colors import make_colors
import argparse
import traceback
import requests
import re
if sys.platform == 'win32':
    import winsound
else:
    if sys.version_info.major == 3:
        from . import winsound_linux as winsound
    else:
        import winsound_linux as winsound
from datetime import datetime
import socket

class notify(object):

    title = "xnotify"
    app = "xnotify"
    event = "xnotify"
    message = "xnotify"
    host = "127.0.0.1"
    port = 23053
    timeout = 10
    icon = None
    active_growl = False
    active_pushbullet = False
    active_nmd = False
    pushbullet_api = False
    nmd_api = False

    configname = os.path.join(os.path.dirname(__file__), 'notify.ini')
    if os.path.isfile('notify.ini'):
        configname = 'notify.ini'
    conf = configset(configname)

    def __init__(self, title = None, app = None, event = None, message = None, host = None, port = None, timeout = None, icon = None, active_pushbullet = True, active_growl = True, active_nmd = True, pushbullet_api = None, nmd_api = None, direct_run = False, gntp_callback = None):
        super(notify, self)
        self.title = title
        self.app = app
        self.event = event
        self.message = message
        self.host = host
        self.port = port
        self.timeout = timeout
        self.icon = None
        self.active_growl = active_growl
        self.active_pushbullet = active_pushbullet
        self.active_nmd = active_nmd
        self.pushbullet_api = pushbullet_api
        self.nmd_api = nmd_api
        self.gntp_callback = gntp_callback
        
        self.configname = os.path.join(os.path.dirname(__file__), 'notify.ini')
        if os.path.isfile('notify.ini'):
            self.configname = 'notify.ini'
        self.conf = configset(self.configname)
        
        if not self.active_growl:
            self.active_growl = self.conf.get_config('service', 'growl', value = '0')
            if self.active_growl:
                self.active_growl = int(self.active_growl)
        if not self.active_pushbullet:
            self.active_pushbullet = self.conf.get_config('service', 'pushbullet', value = '0')
            if self.active_pushbullet:
                self.active_pushbullet = int(self.active_pushbullet)
        if not self.active_nmd:
            self.active_nmd = self.conf.get_config('service', 'nmd', value = '0')
            if self.active_nmd:
                self.active_nmd = int(self.active_nmd)
        if direct_run:
            if active_growl:
                self.growl(title, app, event, message, host, port, timeout, icon)
            if active_nmd:
                self.nmd(title, message)
            if active_pushbullet:
                self.pushbullet(title, message)
        elif self.title and self.event and self.message:
            self.growl(title, app, event, message, host, port, timeout, icon)
        else:
            if self.title and self.message:
                if active_nmd:
                    self.nmd(title, message)
                if active_pushbullet:
                    self.pushbullet(title, message)                    

    @classmethod
    def register(self, app, event, iconpath, timeout=20):
        sendgrowl.growl().register(app, event, iconpath, timeout)
        
    @classmethod
    def set_config(cls, configfile):
        if os.path.isfile(configfile):
            cls.conf = configset(configfile)
            return cls.conf
            
    @classmethod
    def growl(cls, title = None, app = None, event = None, message = None, host = None, port = None, timeout = None, icon = None, iconpath = None, gntp_callback = None):
        if not title:
            title = cls.title
        if not app:
            app = cls.app
        if not event:
            event = cls.event
        if not message:
            message = cls.message
        if not host:
            host = cls.host
        if not port:
            port = cls.port
        if not title:
            title = cls.conf.get_config('growl', 'title')
        if not app:
            app = cls.conf.get_config('growl', 'app')
        if not event:
            event = cls.conf.get_config('growl', 'event')
        if not message:
            message = cls.conf.get_config('growl', 'message')
        if not host:
            host = cls.conf.get_config('growl', 'host')
        if not port:
            port = cls.conf.get_config('growl', 'port')
            if port:
                port = int(port)
        if not timeout:
            timeout = cls.timeout
        if not icon:
            icon = cls.icon

        if isinstance(host, str) and "," in host:
            host_ = re.split(",", host)
            host = []
            for i in host_:
                host.append(i.strip())
        if not host:
            host = '127.0.0.1'
        if not port:
            port = 23053
        if not timeout:
            timeout = 20
        debug(is_growl_active = cls.conf.get_config('service', 'growl'))
        if cls.conf.get_config('service', 'growl', value = 0) == 1 or cls.conf.get_config('service', 'growl', value = 0) == "1" or os.getenv('TRACEBACK_GROWL') == '1' or cls.active_growl:
            growl = sendgrowl.growl()
            error = False

            if isinstance(host, list):
                for i in host:
                    try:
                        growl.publish(app, event, title, message, i, port, timeout, icon, iconpath, gntp_callback)
                        return True
                    except:
                        traceback.format_exc()
                        if os.getenv('DEBUG'):
                            print(make_colors("ERROR [GROWL]:", 'lightwhite', 'lightred', 'blink'))
                            print(make_colors(traceback.format_exc(), 'lightred', 'lightwhite'))
                            error = True
            else:
                try:
                    growl.publish(app, event, title, message, host, port, timeout, icon, iconpath, gntp_callback)
                    return True
                except:
                    traceback.format_exc()
                    if os.getenv('DEBUG'):
                        print(make_colors("ERROR [GROWL]:", 'lightwhite', 'lightred', 'blink'))
                        print(make_colors(traceback.format_exc(), 'lightred', 'lightwhite'))
                    return False
            if error:
                print("ERROR:", True)
                return False
        else:
            print(make_colors("[GROWL]", 'lightwhite', 'lightred') + " " + make_colors('warning: Growl is set True but not active, please change config file to true or 1 or set TRACEBACK_GROWL=1 to activate !', 'lightred', 'lightyellow'))
            return False            

    @classmethod
    def pushbullet(cls, title = None, message = None, api = None, debugx = True):
        if not api:
            api = cls.pushbullet_api
        if not api:
            api = cls.conf.get_config('pushbullet', 'api')
        if not title:
            title = cls.title
        if not title:
            title = cls.conf.get_config('pushbullet', 'title')
        if not message:
            message = cls.message
        if not message:
            message = cls.conf.get_config('pushbullet', 'message')
        if not api:
            if os.getenv('DEBUG') == '1':
                print(make_colors("[Pushbullet]", 'lightwhite', 'lightred') + " " + make_colors('API not Found', 'lightred', 'lightwhite'))
            return False
        if cls.active_pushbullet or cls.conf.get_config('service', 'pushbullet', value = 0) == 1 or cls.active_pushbullet or cls.conf.get_config('service', 'pushbullet', value = 0) == "1" or os.getenv('TRACEBACK_PUSHBULLET') == '1':
            try:
                pb = PB.Pushbullet(api)
                pb.push_note(title, message)
                return True
            except:
                if os.getenv('DEBUG') == '1':
                    print(make_colors("ERROR [PUSHBULLET]:", 'lightwhite', 'lightred', 'blink'))
                    print(make_colors(traceback.format_exc(), 'lightred', 'lightwhite'))
                if os.getenv('DEBUG') == '1':
                    print(make_colors("[Pushbullet]", 'lightwhite', 'lightred') + " " + make_colors('sending error', 'lightred', 'lightwhite'))
                return False
        else:
            print(make_colors("[PUSHBULLET]", 'lightwhite', 'lightred') + " " + make_colors('warning: Pushbullet is set True but not active, please change config file to true or 1 or set TRACEBACK_PUSHBULLET=1 to activate !', 'lightred', 'lightyellow'))
            return False            

    @classmethod
    def nmd(cls, title = None, message = None, api = None, timeout = 3, debugx = True):
        import warnings
        warnings.filterwarnings("ignore")
        url = "https://www.notifymydevice.com/push"#?ApiKey={0}&PushTitle={1}&PushText={2}"
        if not api:
            api = cls.nmd_api
        if not api:
            api = cls.conf.get_config('nmd', 'api')
        if not title:
            title = cls.title
        if not title:
            title = cls.conf.get_config('nmd', 'title')
        if not message:
            message = cls.message
        if not message:
            message = cls.conf.get_config('nmd', 'message')
        if not api:
            if os.getenv('DEBUG') == '1':
                print(make_colors("[NMD]", 'lightwhite', 'lightred') + " " + make_colors('API not Found', 'lightred', 'lightwhite'))
        debug(api = api)
        debug(title = title)
        debug(message = message)
        data = {"ApiKey": api, "PushTitle": title,"PushText": message}
        debug(data = data)
        if cls.active_nmd or cls.conf.get_config('service', 'nmd', value = 0) == 1 or cls.active_nmd or cls.conf.get_config('service', 'nmd', value = 0) == "1" or os.getenv('TRACEBACK_NMD') == '1':
            try:
                a = requests.post(url, data = data, timeout = timeout)
                return a
            except:
                try:
                    a = requests.post(url, data = data, timeout = timeout, verify = False)
                    return a
                except:
                    #traceback.format_exc()
                    if os.getenv('DEBUG') == '1':
                        print(make_colors("ERROR [NMD]:", 'lightwhite', 'lightred', 'blink'))
                        print(make_colors(traceback.format_exc(), 'lightred', 'lightwhite'))
                    if os.getenv('DEBUG') == '1':
                        print(make_colors("[NMD]", 'lightwhite', 'lightred') + " " + make_colors('sending error', 'lightred', 'lightwhite'))
                    return False
        else:
            if os.getenv('DEBUG') == '1':
                print(make_colors("[NMD]", 'lightwhite', 'lightred') + " " + make_colors('warning: NMD is set True but not active, please change config file to true or 1 or set TRACEBACK_NMD=1 to activate !', 'lightred', 'lightyellow'))
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
    def send(cls, title = "this is title", message = "this is message", app = None, event = None, host = None, port = None, timeout = None, icon = None, pushbullet_api = None, nmd_api = None, growl = True, pushbullet = False, nmd = False, debugx = True, iconpath=None, gntp_callback = None):
        if cls.title and not title:
            title = cls.title
        if cls.message and not message:
            message = cls.message
        if cls.app and not app:
            app = cls.app
        if cls.event and not event:
            event = cls.event
        if cls.host and not host:
            host = cls.host
        if cls.port and not port:
            port = cls.port
        if cls.timeout and not timeout:
            timeout = cls.timeout
        
        if cls.icon and not icon:
            icon = cls.icon
        if cls.pushbullet_api and not pushbullet_api:
            pushbullet_api = cls.pushbullet_api
        if cls.nmd_api and not nmd_api:
            nmd_api = cls.nmd_api
        
        if growl or cls.conf.get_config('service', 'growl', '1') == '1' or cls.conf.get_config('service', 'growl', '1') == 1:
            cls.growl(title, app, event, message, host, port, timeout, icon, iconpath, gntp_callback)
        if pushbullet or cls.conf.get_config('service', 'pushbullet', '0') == '1' or cls.conf.get_config('service', 'pushbullet', '0') == 1:
            cls.pushbullet(title, message, pushbullet_api, debugx)
        if nmd or cls.conf.get_config('service', 'nmd', '0') == '1' or cls.conf.get_config('service', 'nmd', '0') == 1:
            cls.nmd(title, message, nmd_api, debugx = debugx)
        cls.client(title, message)

    @classmethod
    def server(cls, host = '0.0.0.0', port = 33000):
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
                port), 'black', 'lightcyan'))            
            while True:
                try:
                    #s.listen(8096) #TCP
                    #conn, addr = s.accept() #TCP
                    data, addr = s.recvfrom(8096)

                    if data:
                        #data = conn.recv(8096) #TCP
                        title = ''
                        message = ''
                        data_title = re.findall('.*?title:(.*?)message:', data)
                        if data_title:
                            title = data_title[0].strip()
                        data_message = re.findall('.*?message:(.*?)$', data)
                        if data_message:
                            message = data_message[0].strip()
                        date = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S%f')

                        if title and message:
                            print(make_colors(date, 'lightyellow') + " - " + make_colors("title =>", 'black', 'lightgreen') + " " + make_colors(str(title), 'lightgreen') + " " + make_colors("message =>", 'lightwhite', 'lightblue') + " " + make_colors(message, 'lightblue'))
                            if active_sound and sound:
                                winsound.PlaySound(sound, winsound.SND_ALIAS)
                            #try:
                                #self.notify(title, message, "Notify", "Receive", debugx = False)
                            #except:
                                #pass
                        #print("data =", data)
                        #print("title =", title)
                        #print("message =", message)

                except:
                    traceback.format_exc()
                    sys.exit()
        except:
            traceback.format_exc()
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
        parser.add_argument('-g', '--growl', action = 'store_true', help = 'Active Growl')
        parser.add_argument('-p', '--pushbullet', action = 'store_true', help = 'Active Pushbullet')
        parser.add_argument('-n', '--nmd', action = 'store_true', help = 'Active NotifyMyAndroid')
        parser.add_argument('-papi', '--pushbullet-api', action = 'store', help = 'Pushbullet API')
        parser.add_argument('-pnmd', '--nmd-api', action = 'store', help = 'NotifyMyAndroid API')
        parser.add_argument('-a', '--app', action = 'store', help = 'App Name for Growl')
        parser.add_argument('-e', '--event', action = 'store', help = 'Event Name for Growl')
        parser.add_argument('-i', '--icon', action = 'store', help = 'Icon Path for Growl')
        parser.add_argument('-H', '--host', action = 'store', help = 'Host for Growl and Snarl')
        parser.add_argument('-P', '--port', action = 'store', help = 'Port for Growl and Snarl')
        parser.add_argument('-t', '--timeout', action = 'store', help = 'Timeout for Growl and Snarl')
        parser.add_argument('TITLE', action = 'store', help = 'Title of Message')
        parser.add_argument('MESSAGE', action = 'store', help = 'Message')
        parser.add_argument('-s', '--server', action = 'store_true', help = 'start server')
        parser.add_argument('-c', '--client', action = 'store_true', help = 'start test client')

        if len(sys.argv) == 1:
            parser.print_help()

        else:
            if '-s' in sys.argv[1:]:
                cls.server()
            else:
                args = parser.parse_args()

                if args.growl:
                    cls.growl(args.TITLE, args.app, args.event, args.MESSAGE, args.host, args.port, args.timeout, args.icon)
                elif args.pushbullet:
                    #print("type =", type(cls.pushbullet))
                    cls.pushbullet(args.TITLE, args.MESSAGE, args.pushbullet_api)
                elif args.nmd:
                    cls.nmd(args.TITLE, args.MESSAGE, args.nmd_api)
                else:
                    cls.notify(args.TITLE, args.MESSAGE, args.app, args.event, args.host, args.port, args.timeout, args.icon, args.pushbullet_api, args.nmd_api)
                if args.server:
                    cls.server()
                if args.client:
                    cls.client('this is title', 'this is message !')
                #self.client(args.TITLE, args.MESSAGE)

def usage():
    c = notify()
    c.usage()

if __name__ == '__main__':
    usage()
    #c.server()
    #c.test_client()
