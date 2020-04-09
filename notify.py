#!c:/SDK/Anaconda2/python.exe
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

class notify(object):
    def __init__(self, title = None, app = None, event = None, message = None, host = None, port = None, timeout = None, icon = None, active_pushbullet = True, active_growl = True, active_nmd = True, pushbullet_api = None, nmd_api = None):
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
        
        self.configname = os.path.join(os.path.dirname(__file__), 'notify.ini')
        if os.path.isfile('notify.ini'):
            self.configname = 'notify.ini'
        self.conf = configset(self.configname)
        
        if not self.active_growl:
            self.active_growl = self.conf.get_config('service', 'growl', value = '0')
            self.active_growl = int(self.active_growl)
        if not self.active_pushbullet:
            self.active_pushbullet = self.conf.get_config('service', 'pushbullet', value = '0')
            self.active_pushbullet = int(self.active_pushbullet)
        if not self.active_nmd:
            self.active_nmd = self.conf.get_config('service', 'nmd', value = '0')
            self.active_nmd = int(self.active_nmd)
        
    def growl(self, title = None, app = None, event = None, message = None, host = None, port = None, timeout = None, icon = None):
        if not title:
            title = self.title
        if not app:
            app = self.app
        if not event:
            event = self.event
        if not message:
            message = self.message
        if not host:
            host = self.host
        if not port:
            port = port
        if not title:
            title = self.conf.get_config('growl', 'title')
        if not app:
            app = self.conf.get_config('growl', 'app')
        if not event:
            event = self.conf.get_config('growl', 'event')
        if not message:
            message = self.conf.get_config('growl', 'message')
        if not host:
            host = self.conf.get_config('growl', 'host')
        if not port:
            port = self.conf.get_config('growl', 'port')
            if port:
                port = int(port)
        if not timeout:
            timeout = self.timeout
        if not icon:
            icon = self.icon
        
        if not host:
            host = '127.0.0.1'
        if not port:
            port = 23053
        if not timeout:
            timeout = 20
                
        if self.active_growl or self.conf.get_config('service', 'growl', value = 0) == "1":
            growl = sendgrowl.growl()
            try:
                growl.publish(app, event, title, message, host, port, timeout, iconpath = icon)
                return True
            except:
                if os.getenv('DEBUG'):
                    print(make_colors("ERROR [GROWL]:", 'lightwhite', 'lightred', 'blink'))
                    print(make_colors(traceback.format_exc(), 'lightred', 'lightwhite'))
                return False
        else:
            print(make_colors("[GROWL]", 'lightwhite', 'lightred') + " " + make_colors('warning: Growl not actieve', 'lightred', 'lightyellow'))
            return False            
            
    def pushbullet(self, title = None, message = None, api = None):
        if not api:
            api = self.pushbullet_api
        if not api:
            api = self.conf.get_config('pushbullet', 'api')
        if not title:
            title = self.title
        if not title:
            title = self.conf.get_config('pushbullet', 'title')
        if not message:
            message = self.message
        if not message:
            message = self.conf.get_config('pushbullet', 'message')
        if not api:
            print(make_colors("[Pushbullet]", 'lightwhite', 'lightred') + " " + make_colors('API not Found', 'lightred', 'lightwhite'))
            return False
        if self.active_pushbullet or self.conf.get_config('service', 'pushbullet', value = 0) == "1":
            try:
                pb = PB.Pushbullet(api)
                pb.push_note(title, message)
                return True
            except:
                if os.getenv('DEBUG'):
                    print(make_colors("ERROR [PUSHBULLET]:", 'lightwhite', 'lightred', 'blink'))
                    print(make_colors(traceback.format_exc(), 'lightred', 'lightwhite'))
                print(make_colors("[Pushbullet]", 'lightwhite', 'lightred') + " " + make_colors('sending error', 'lightred', 'lightwhite'))
                return False
        else:
            print(make_colors("[PUSHBULLET]", 'lightwhite', 'lightred') + " " + make_colors('warning: Pushbullet not actieve', 'lightred', 'lightyellow'))
            return False            
        
    def nmd(self, title = None, message = None, api = None):
        url = "https://www.notifymydevice.com/push"#?ApiKey={0}&PushTitle={1}&PushText={2}"
        if not api:
            api = self.nmd_api
        if not api:
            api = self.conf.get_config('nmd', 'api')
        if not title:
            title = self.title
        if not title:
            title = self.conf.get_config('nmd', 'title')
        if not message:
            message = self.message
        if not message:
            message = self.conf.get_config('nmd', 'message')
        if not api:
            print(make_colors("[NMD]", 'lightwhite', 'lightred') + " " + make_colors('API not Found', 'lightred', 'lightwhite'))
        debug(api = api)
        debug(title = title)
        debug(message = message)
        data = {"ApiKey": api, "PushTitle": title,"PushText": message}
        debug(data = data)
        if self.active_nmd or self.conf.get_config('service', 'nmd', value = 0) == "1":
            try:
                a = requests.post(url, data = data)
                return a
            except:
                if os.getenv('DEBUG'):
                    print(make_colors("ERROR [PUSHBULLET]:", 'lightwhite', 'lightred', 'blink'))
                    print(make_colors(traceback.format_exc(), 'lightred', 'lightwhite'))
                print(make_colors("[NMD]", 'lightwhite', 'lightred') + " " + make_colors('sending error', 'lightred', 'lightwhite'))
                return False
        else:
            print(make_colors("[NMD]", 'lightwhite', 'lightred') + " " + make_colors('warning: NMD not actieve', 'lightred', 'lightyellow'))
            return False
        
    def notify(self, title = None, message = None, app = None, event = None, host = None, port = None, timeout = None, icon = None, pushbullet_api = None, nmd_api = None, growl = True, pushbullet = True, nmd = True):
        if growl:
            self.growl(title, app, event, message, host, port, timeout, icon)
        if pushbullet:
            self.pushbullet(title, message, pushbullet_api)
        if nmd:
            self.nmd(title, message, nmd_api)
            
    def usage(self):
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
        
        if len(sys.argv) == 1:
            parser.print_help()
        else:
            args = parser.parse_args()
            if args.growl:
                self.growl(args.TITLE, args.app, args.event, args.MESSAGE, args.host, args.port, args.timeout, args.icon)
            if args.pushbullet:
                #print("type =", type(self.pushbullet))
                self.pushbullet(args.TITLE, args.MESSAGE, args.pushbullet_api)
            if args.nmd:
                self.nmd(args.TITLE, args.MESSAGE, args.nmd_api)
                
if __name__ == '__main__':
    c = notify()
    c.usage()