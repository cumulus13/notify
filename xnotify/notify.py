#!/usr/bin/env python2
from __future__ import print_function
import sys, os
from pprint import pprint
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
from gntplib import Publisher, Resource
#sys.exc_info = traceback.format_exception

class notify(object):

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

    configname = os.path.join(os.path.dirname(__file__), 'notify.ini')
    if os.path.isfile('notify.ini'):
        configname = 'notify.ini'
    try:
        conf = configset(configname)
    except:
        conf = configset.configset(configname)

    def __init__(self, title = None, app = None, event = None, message = None, host = None, port = None, timeout = None, icon = None, active_pushbullet = True, active_growl = True, active_nmd = True, pushbullet_api = None, nmd_api = None, direct_run = False, gntp_callback = None, active_ntfy = True, ntfy_server = None):
        super(notify, self)
        self.title = title or self.title
        self.app = app or self.app
        self.event = event or self.event
        self.message = message or self.message
        self.host = host or self.host
        self.port = port or self.port
        self.timeout = timeout or self.timeout
        self.icon = None or self.icon
        self.active_growl = active_growl or self.conf.get_config('service', 'growl', '1') or self.active_growl
        self.active_pushbullet = active_pushbullet or self.conf.get_config('service', 'pushbullet', '1') or self.active_pushbullet
        self.active_nmd = active_nmd or self.conf.get_config('service', 'nmd', '1') or self.active_nmd
        self.active_ntfy = active_ntfy or self.active_ntfy
        self.pushbullet_api = pushbullet_api or self.pushbullet_api or self.conf.get_config('pushbullet', 'api')
        self.nmd_api = nmd_api or self.nmd_api or self.conf.get_config('nmd', 'api')
        self.gntp_callback = gntp_callback or self.gntp_callback
        self.ntfy_server = ntfy_server or self.ntfy_server
        
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
            self.conf = configset.configset(self.configname)
        
        if self.title and self.message and (self.active_growl or self.active_pushbullet or self.active_nmd or self.active_ntfy):
            if active_growl: self.growl(title, app, event, message, host, port, timeout, icon)
            if active_nmd and self.nmd_api: self.nmd(title, message)
            if active_pushbullet and self.pushbullet_api: self.pushbullet(title, message)
        #elif self.title and self.event and self.message:
            #self.growl(title, app, event, message, host, port, timeout, icon)
        #elif self.title and self.message:
            #if active_nmd:
                #self.nmd(title, message)
            #if active_pushbullet:
                #self.pushbullet(title, message)
        if not self.title: self.title = 'xnotify'
        if not self.message: self.message = 'xnotify'
        if not self.app: self.app = 'xnotify'
        if not self.event: self.event = 'xnotify'

    @classmethod
    def register(self, app, event, iconpath, timeout=20):
        '''
            Growl only
        '''        
        debug(app = app)
        debug(event = event)
        debug(iconpath = iconpath)
        debug(timeout = timeout)
        
        s = sendgrowl.growl(app, event, iconpath, timeout = timeout)
        s.register()
        
    @classmethod
    def set_config(cls, configfile):
        if os.path.isfile(configfile):
            cls.conf = configset(configfile)
            return cls.conf
            
    @classmethod
    def _ntfy(cls, data, **kwargs):
        debug(server = kwargs.get('server'))
        if kwargs.get('server'):
            if isinstance(kwargs.get('server'), list):
                for i in kwargs.get('server'):
                    if not 'http' == i[:4]:
                        i = 'http://' + i
                    try:
                        a = requests.post(i, data = data)
                        debug(a = a, debug = 1)
                        debug(content = a.content, debug = 1)
                    except:
                        print(traceback.format_exc())
            else:
                a = requests.post(kwargs.get('server'), data = data)
                debug(a = a)
                debug(content = a.content)                
        return True
                
    @classmethod
    def ntfy(cls, app, title, message, icon = None, server = None, priority = None, tags = [], click = None, attach = None, action = None, email = None, filename = None):
        url = server or cls.ntfy_server or cls.conf.get_config('ntfy', 'server') or 'https://ntfy.sh/'
        debug(url = url)
        if "," in url:
            url = str(url).split(",")
            url = [i.strip() for i in url]
        debug(url = url)
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
        debug(data = data, debug = 1)
        a = cls._ntfy(data, app = app, title = title, message = message, icon = icon, priority = priority, tags = tags, click = click, attach = attach, action = action, email = email, filename = filename, server = url)
        #a = requests.post(url, data = data)
        #debug(a = a)
        #debug(content = a.content)
        return a
    
    @classmethod
    def growl(cls, title = None, app = None, event = None, message = None, host = None, port = None, timeout = None, icon = None, iconpath = None, gntp_callback = None):
        if not title: title = cls.title
        if not app: app = cls.app
        if not event: event = cls.event
        if not message: message = cls.message
        if not host: host = cls.host
        if not port: port = cls.port
        if not title: title = cls.conf.get_config('growl', 'title')
        if not app: app = cls.conf.get_config('growl', 'app')
        if not event: event = cls.conf.get_config('growl', 'event')
        if not message: message = cls.conf.get_config('growl', 'message')
        if not host: host = cls.conf.get_config('growl', 'host')
        if not port:
            port = cls.conf.get_config('growl', 'port')
            if port:
                port = int(port)
        if not timeout:
            timeout = cls.timeout
        debug(icon = icon)
        if not icon: icon = cls.icon or cls.conf.get_config('growl', 'icon')
        debug(icon = icon)
        if iconpath and not icon:
            icon = iconpath
        if icon:
            if not os.path.isfile(icon): icon = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.basename(icon))
        else:
            icon = cls.conf.get_config('growl', 'icon')
        if icon: icon = os.path.realpath(icon)
        debug(icon = icon)
        if os.path.isfile(icon):
            iconpath = icon
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
            if not isinstance(host, list): host = [host]
            growl = sendgrowl.Growl(app, event, icon)
            error = False
            debug(event = event)
            debug(title = title)
            debug(message = message)
            debug(icon = icon)
            debug(iconpath = iconpath)
            debug(host = host)
            debug(timeout = timeout)
            debug(gntp_callback = gntp_callback)
            debug(growl_file = sendgrowl.__file__)
            try:
                growl.Publish(event, title, message, host = host, port = port, timeout = timeout, icon = icon, iconpath = iconpath, gntp_callback = gntp_callback, app = app)
            except:
                print(traceback.format_exc())
                error = True
            
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
    def nmd(cls, title = None, message = None, api = None, debugx = True, timeout = 3):
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
    def send(cls, title = "this is title", message = "this is message", app = None, event = None, host = None, port = None, timeout = None, icon = None, pushbullet_api = None, nmd_api = None, growl = True, pushbullet = False, nmd = False, ntfy = True, debugx = True, iconpath=None, gntp_callback = None, ntfy_servers = None, **kwargs):
        debug(ntfy_servers = ntfy_servers)
        debug(host = host)
        title = title or cls.title or 'xnotify'
        message = message or cls.message
        app = app or cls.app or 'xnotify'
        event = event or cls.event or 'xnotify'
        host = host or cls.conf.get_config_as_list('growl','host') or cls.host or '127.0.0.1'
        debug(host = host)
        port = port or cls.port or 5432
        timeout = timeout or cls.timeout or 20
        icon = icon or cls.icon
        pushbullet_api = pushbullet_api or cls.pushbullet_api or cls.conf.get_config('pushbullet', 'api')
        nmd_api = nmd_api or cls.nmd_api or cls.conf.get_config('nmd', 'api')
        
        if growl or cls.conf.get_config('service', 'growl', '1') == '1' or cls.conf.get_config('service', 'growl', '1') == 1:
            print("send to growl ..")
            #cls.growl(title, app, event, message, host, port, timeout, icon, iconpath, gntp_callback)
            p1 = Process(target = cls.growl, args = (title, app, event, message, host, port, timeout, icon, iconpath, gntp_callback))
            p1.start()
        if pushbullet or cls.conf.get_config('service', 'pushbullet', '0') == '1' or cls.conf.get_config('service', 'pushbullet', '0') == 1:
            print("send to pushbullet ...")
            if cls.conf.get_config('pushbullet', 'api'):
                #cls.pushbullet(title, message, pushbullet_api, debugx)
                p2 = Process(target = cls.pushbullet, args = (title, message, pushbullet_api, debugx))
                p2.start()
            else:
                print("pushbullet is active but no API !")
            
        if nmd or cls.conf.get_config('service', 'nmd', '0') == '1' or cls.conf.get_config('service', 'nmd', '0') == 1:
            print("send to nmd ...")
            if cls.conf.get_config('nmd', 'api'):
                #cls.nmd(title, message, nmd_api, debugx = debugx)
                p3 = Process(target = cls.nmd, args = (title, message, nmd_api, debugx))
                p3.start()
            else:
                print("NMD is active but no API !")
        debug(ntfy = ntfy)
        if ntfy or cls.conf.get_config('service', 'nfty', '0') == '1' or cls.conf.get_config('service', 'nfty', '0') == 1:
            print("send to ntfy ...")
            ntfy_icon = None
            if icon or iconpath:
                try:
                    if 'http' == icon[:4]:
                        ntfy_icon = icon
                except:
                    pass
                try:
                    if 'http' == iconpath[:4]:
                        ntfy_icon = iconpath
                except:
                    pass
            debug(ntfy_servers = ntfy_servers)
            #cls.ntfy(app, title, message, ntfy_icon, server = ntfy_servers)
            p4 = Process(target = cls.ntfy, args = (app, title, message, ntfy_icon, ntfy_servers))
            p4.start()
            
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
        parser.add_argument('-H', '--host', action = 'store', help = 'Host for Growl and Snarl', nargs = '*')
        parser.add_argument('-P', '--port', action = 'store', help = 'Port for Growl and Snarl')
        parser.add_argument('-t', '--timeout', action = 'store', help = 'Timeout for Growl and Snarl')
        parser.add_argument('TITLE', action = 'store', help = 'Title of Message')
        parser.add_argument('MESSAGE', action = 'store', help = 'Message')
        parser.add_argument('-s', '--server', action = 'store_true', help = 'start server')
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
                elif args.ntfy:
                    cls.ntfy(args.app, args.TITLE, args.MESSAGE, args.ntfy_icon, args.ntfy_priority, args.ntfy_tags, args.ntfy_click, args.ntfy_attach, None, args.ntfy_email, args.ntfy_filename, server=args.ntfy_hosts)
                else:
                    debug(args_ntfy_hosts = args.ntfy_hosts)
                    cls.send(args.TITLE, args.MESSAGE, args.app, args.event, args.host, args.port, args.timeout, args.icon, args.pushbullet_api, args.nmd_api, ntfy_servers = args.ntfy_hosts)
                if args.server:
                    cls.server()
                if args.client:
                    cls.client('this is title', 'this is message !')
                #self.client(args.TITLE, args.MESSAGE)

def usage():
    c = notify()
    c.usage()

if __name__ == '__main__':
    #notify.ntfy('battmon', 'test from python', "FULL", "https://www.clipartmax.com/png/small/457-4573861_512-x-512-1-battery-full-icon-png.png")
    #notify.ntfy('battmon', 'test from python', "FULL", "c:\PROJECTS\battmon\icon.png")
    usage()
    #c.server()
    #c.test_client()

# by LICFACE <licface@yahoo.com>
