#!/usr/bin/env python2
from __future__ import print_function
import sys, os
import argparse
from configset import configset
import pushbullet as PB
import sendgrowl
if os.environ.get('DEBUG') or os.environ.get('DEBUG_SERVER'):
    from pydebugger.debug import debug
else:
    def debug(*args, **kwargs):
        return ''
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

    def __init__(self, title = None, app = None, event = None, message = None, host = None, port = None, timeout = None, icon = None, active_pushbullet = True, active_growl = True, active_nmd = True, pushbullet_api = None, nmd_api = None, direct_run = False, gntp_callback = None, active_ntfy = True, ntfy_server = None, sticky = False, ntfy_icon = '', syslog = True, syslog_server = []):
        super(notify, self)
        self.title = title or self.title or 'xnotify'
        self.app = app or self.app or 'xnotify'
        if isinstance(event, str):
            self.event.append(event)
        else:
            if not event:
                self.event = []
            else:
                self.event += event
        self.event = self.event or ['xnotify']
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
        self.sticky = sticky or self.sticky or self.conf.get_config('growl', 'sticky') or False
        self.ntfy_icon = ntfy_icon or self.ntfy_icon
        self.syslog = syslog or self.syslog
        self.syslog_server = syslog_server or self.syslog_server or ['127.0.0.1:514']
        
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

        try:
            s = sendgrowl.growl(app, event, iconpath, timeout = timeout)
        except:
            self.logger(str(traceback.format_exc()), 'error')
        try:
            s.register()
        except:
            self.logger(str(traceback.format_exc()), 'error')

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
                        pass
                    except:
                        self.logger(str(traceback.format_exc()), 'error')
                        print(traceback.format_exc())
            else:
                try:
                    a = requests.post(kwargs.get('server'), data = data)
                    debug(a = a)
                    debug(content = a.content)                
                except requests.exceptions.ConnectionError:
                    print(make_colors("[NTFY]", 'lw', 'm') + " " + make_colors('No Internet Connection !', 'lw', 'r'))
                except:
                    self.logger(str(traceback.format_exc()), 'error')
                    print(traceback.format_exc())
                
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
    def growl(cls, title = None, app = None, event = None, message = '', host = None, port = None, timeout = None, icon = None, iconpath = None, gntp_callback = None, sticky = False):
        title = title or cls.title or cls.conf.get_config('growl', 'title')
        app = app or cls.app or cls.conf.get_config('growl', 'app')
        message = message or cls.message
        event = event or cls.event or cls.conf.get_config('growl', 'event')
        host = host or cls.host or cls.conf.get_config('growl', 'host') or ['127.0.0.1']
        port = port or cls.port or cls.conf.get_config('growl', 'port') or 23053
        sticky = sticky or cls.sticky or cls.conf.get_config('growl', 'sticky')
        timeout = timeout or cls.timeout or cls.conf.get_config('growl', 'timeout')
        icon = icon or iconpath or cls.icon or cls.conf.get_config('growl', 'icon')
        iconpath = iconpath or icon or cls.icon or cls.conf.get_config('growl', 'icon')
        debug(icon = icon)
        debug(iconpath = iconpath)
        debug(host = host)
        
        if host and isinstance(host, str): host = list(filter(None, [i.split() for i in re.split(",|\n", host)])) or ['127.0.0.1']
        debug(is_growl_active = cls.conf.get_config('service', 'growl'))
        if cls.conf.get_config('service', 'growl', value = 0) == 1 or cls.conf.get_config('service', 'growl', value = 0) == "1" or os.getenv('GROWL') == '1' or cls.active_growl:
            if not isinstance(host, list): host = [host]
            if not isinstance(event, list):
                EVENT = [event]
            else:
                EVENT = event
            growl = sendgrowl.Growl(app, EVENT, icon)
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
                growl.Publish(event, title, message, host = host, port = port, timeout = timeout, icon = icon, iconpath = iconpath, gntp_callback = gntp_callback, app = app, sticky = sticky)
            except:
                #print(traceback.format_exc(syslog = 0))
                traceback.format_exc(syslog = 0, growl = 0)
                error = True

            if error:
                print("ERROR:", True)
                return False
        else:
            print(make_colors("[GROWL]", 'lightwhite', 'lightred') + " " + make_colors('warning: Growl is set True but not active, please change config file to true or 1 or set GROWL=1 to activate !', 'lightred', 'lightyellow'))
            return False            

    @classmethod
    def pushbullet(cls, title = None, message = None, api = None, debugx = True):
        api = api or cls.pushbullet_api or cls.conf.get_config('pushbullet', 'api')
        title = title or cls.title or cls.conf.get_config('pushbullet', 'title')
        message = message or cls.message or cls.conf.get_config('pushbullet', 'message')
        if not api:
            if os.getenv('DEBUG') == '1':
                print(make_colors("[Pushbullet]", 'lightwhite', 'lightred') + " " + make_colors('API not Found', 'lightred', 'lightwhite'))
            return False
        if cls.active_pushbullet or cls.conf.get_config('service', 'pushbullet', value = 0) == 1 or cls.active_pushbullet or cls.conf.get_config('service', 'pushbullet', value = 0) == "1" or os.getenv('PUSHBULLET') == '1':
            try:
                pb = PB.Pushbullet(api)
                pb.push_note(title, message)
                return True
            except:
                cls.logger(str(traceback.format_exc(growl = 0, syslog = 0)), 'error')                
                print("send to pushbullet ERROR !, see log file. '{}'".format(cls.logfile))                
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
        api = api or cls.nmd_api or cls.conf.get_config('nmd', 'api')
        title = title or cls.title or cls.conf.get_config('nmd', 'title')
        message = message or cls.message or cls.conf.get_config('nmd', 'message')
        if not api:
            if os.getenv('DEBUG') == '1':
                print(make_colors("[NMD]", 'lightwhite', 'lightred') + " " + make_colors('API not Found', 'lightred', 'lightwhite'))
        debug(api = api)
        debug(title = title)
        debug(message = message)
        data = {"ApiKey": api, "PushTitle": title,"PushText": message}
        debug(data = data)
        if cls.active_nmd or cls.conf.get_config('service', 'nmd', value = 0) == 1 or cls.active_nmd or cls.conf.get_config('service', 'nmd', value = 0) == "1" or os.getenv('NMD') == '1':
            try:
                a = requests.post(url, data = data, timeout = timeout)
                return a
            except:
                try:
                    a = requests.post(url, data = data, timeout = timeout, verify = False)
                    return a
                except:
                    #traceback.format_exc()
                    cls.logger(str(traceback.format_exc(growl = 0, syslog = 0)), 'error')                
                    
                    if os.getenv('DEBUG') == '1' or os.getenv('TRACEBACK') == '1':
                        print("send to NMD ERROR !, see log file. '{}'".format(cls.logfile))                    
                        print(make_colors("ERROR [NMD]:", 'lightwhite', 'lightred', 'blink'))
                        print(make_colors(traceback.format_exc(), 'lightred', 'lightwhite'))
                    else:
                        traceback.format_exc()
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
    def send(cls, title = "this is title", message = "this is message", app = None, event = None, host = None, port = None, timeout = None, icon = None, pushbullet_api = None, nmd_api = None, growl = True, pushbullet = False, nmd = False, ntfy = True, debugx = True, iconpath=None, gntp_callback = None, ntfy_servers = None, sticky = False, ntfy_icon = '', syslog = True, syslog_server = [], server_host = None, server_port = None, to_server_only = False, message_color = None, syslog_severity = 'info', syslog_facility = 'daemon', **kwargs):
        debug(cls_server_as_router = cls.server_as_router)
        if not cls.server_as_router:
            cls.client(title, (message_color or message))
        if to_server_only:
            return True
        p1 = p2 = p3 = p4 = None
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
        sticky = sticky or cls.sticky
        ntfy_icon = ntfy_icon or cls.ntfy_icon
        debug(cls_syslog = cls.syslog)
        syslog = syslog or cls.syslog
        syslog_server = syslog_server or cls.syslog_server
        server_host = server_host or '0.0.0.0'
        server_port = server_port or 33000
        
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
            debug(iconpath = iconpath)
            debug(gntp_callback = gntp_callback)
            #cls.growl(title, app, event, message, host, port, timeout, icon, iconpath, gntp_callback)
            
            try:
                p1.terminate()
            except:
                pass
            try:
                p1 = Process(target = cls.growl, args = (title, app, event, message, host, port, timeout, icon, iconpath, gntp_callback, sticky))
                p1.start()
            except:
                try:
                    cls.growl(title, app, event, message, host, port, timeout, icon, iconpath, gntp_callback, sticky)
                except:
                    cls.logger(traceback.format_exc(growl = 0, syslog = 0), 'error')
                    print("error send message to growl ! [see log file !]")
                traceback.format_exc(syslog = 0, growl = 1)
            if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", make_colors("growl error", 'lw', 'r'))
            
        if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", "pushbullet:", (pushbullet and (cls.conf.get_config('service', 'pushbullet', '0') == '1' or cls.conf.get_config('service', 'pushbullet', '0') == 1)) or os.getenv('PUSHBULLET') == '1')
        if (pushbullet and (cls.conf.get_config('service', 'pushbullet', '0') == '1' or cls.conf.get_config('service', 'pushbullet', '0') == 1)) or os.getenv('PUSHBULLET') == '1':
            if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", "send to pushbullet ...")
            if pushbullet_api or cls.conf.get_config('pushbullet', 'api'):
                #cls.pushbullet(title, message, pushbullet_api, debugx)
                
                try:
                    p2 = Process(target = cls.pushbullet, args = (title, message, pushbullet_api, debugx))
                    p2.start()
                except:
                    try:
                        cls.pushbullet(title, message, pushbullet_api, debugx)
                    except:
                        cls.logger(traceback.format_exc(growl = 0, syslog = 0), 'error')
                        print("error send message to pushbullet ! [see log file !]")
                    
                    traceback.format_exc(syslog = 0, growl = 0)
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
                    
                    traceback.format_exc(syslog = 0, growl = 0)
                if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", make_colors("nmd error", 'lw', 'r'))
                
            else:
                print(make_colors("NMD is active but no API !", 'b', 'y'))
        debug(ntfy = ntfy)
        
        if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", "ntfy:", (ntfy and (cls.conf.get_config('service', 'ntfy', '0') == '1' or cls.conf.get_config('service', 'ntfy', '0') == 1)) or os.getenv('NTFY') == '1')
        if (ntfy and (cls.conf.get_config('service', 'ntfy', '0') == '1' or cls.conf.get_config('service', 'ntfy', '0') == 1)) or os.getenv('NTFY') == '1':
            if os.getenv('XNOTIFY_DEBUG') == '1': print("[XNOTIFY_DEBUG]", "send to ntfy ...")
            ntfy_icon = None
            if ntfy_icon or icon or iconpath:
                try:
                    if 'http' == icon[:4]:
                        ntfy_icon = icon
                except:
                    pass
                    #traceback.format_exc(syslog = 0, growl = 0)
                try:
                    if 'http' == iconpath[:4]:
                        ntfy_icon = iconpath
                except:
                    pass
                    #traceback.format_exc(syslog = 0, growl = 0)
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
                
                traceback.format_exc(syslog = 0, growl = 0)
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
        parser.add_argument('TITLE', action = 'store', help = 'Title of Message')
        parser.add_argument('MESSAGE', action = 'store', help = 'Message')
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
                
                if args.to_server_only:
                    cls.syslog = False
                    cls.active_growl = False
                    cls.active_nmd = False
                    cls.active_pushbullet = False
                    cls.active_ntfy = False
                
                gntp_callback = None
                if args.callback:
                    gntp_callback = eval(args.callback)

                if args.growl and not args.to_server_only:
                    cls.growl(args.TITLE, args.app, args.event, args.MESSAGE, args.growl_host, args.growl_port, args.timeout, args.icon)
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
                        cls.send(args.TITLE, args.MESSAGE, args.app, args.event, args.growl_host, args.growl_port, args.timeout, args.icon, args.pushbullet_api, args.nmd_api, args.no_growl, args.no_pushbullet, args.no_nmd, args.no_ntfy, args.debug, args.icon, gntp_callback, args.ntfy_hosts, args.sticky, args.ntfy_icon, args.no_syslog, args.syslog_server, server_host, args.server_port, args.to_server_only)

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

