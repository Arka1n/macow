#!/usr/bin/python3
import sys
from sys import stdout
import os
import signal
import argparse
import time
import urllib.request
from multiprocessing import Process
from sarge import run, Capture
from selenium import webdriver
from colorama import init, Style as S, Fore as Co
init()

# CHECKS #

if not os.geteuid() == 0:
    print(C.RED + """                          
        _______________
        |             |
        | GOT ROOT !? |
        |_____________|            
            """)
    quit() 

## INIT ##

parser = argparse.ArgumentParser(description='/// Macow, the MAC obfuscating wrapper ! ///', epilog='Ex : sudo python3 macow.py -M 1 -E "1337" -LOG wlan0 # Anonymise MAC and connect back to 1337 every 1 min while logging on webpage')
parser.add_argument('-R','-r', action='store_true', help=': Anonymise MAC')
parser.add_argument('-S','-s', metavar='<MAC>', help=': Set MAC for interface')
parser.add_argument('-U','-u', action='store_true', help=': Undo changes to MAC adress')
parser.add_argument('-M','-m', metavar='<MINUTES>', help=': Anonymise MAC every X minutes')
parser.add_argument('-H', metavar='<HOURS>', help=': Anonymise MAC every X hours')
parser.add_argument('-D','-d', metavar='<DAYS>', help=': Anonymise MAC every X days')
parser.add_argument('-E','-e', metavar='"<ESSID>"', help=': Essid of the AP you want to reconnect to')
parser.add_argument('-P','-p', metavar='"<PASSWORD>"', help=': Password of the AP')
parser.add_argument('-LOG','-log', action='store_true', help=': Log on webpage')
parser.add_argument('-SHOW','-show', action='store_true', help=': Show current MAC adress')
parser.add_argument('IFACE', metavar='<IFACE>', help=': Name of the interface')
parser.add_argument('-EDIT','-edit', action='store_true', help=': Manage macow profiles')
args = parser.parse_args()

choices_nope = ['NO', 'No', 'N', 'n', 'no', 'Nope', 'NOPE']
choices_yes = ['YES', 'Yes', 'Y', 'y', 'yes', 'Yup', 'YUP']

nm_modified = False

if sys.platform == "linux":
    macowfolder = str('/home/' + os.path.expanduser(os.environ["SUDO_USER"]) + '/.macow/') ## Get user's home path for tempfolder
    macow_data_folder = str('/home/' + os.path.expanduser(os.environ["SUDO_USER"]) + '/.macow/Data/')
    macow_profiles_folder = str('/home/' + os.path.expanduser(os.environ["SUDO_USER"]) + '/.macow/Profiles/')
elif sys.platform == "darwin":
    macowfolder = str('/Users/' + os.path.expanduser(os.environ["SUDO_USER"]) + '/macow/') ## Get user's home path for tempfolder
    macow_data_folder = str('/Users/' + os.path.expanduser(os.environ["SUDO_USER"]) + '/macow/Data/')
    macow_profiles_folder = str('/Users/' + os.path.expanduser(os.environ["SUDO_USER"]) + '/macow/Profiles/')

macow_dir = str(macowfolder)
macow_data_dir = str(macow_data_folder)
macow_profiles_dir = str(macow_profiles_folder)

if not os.path.exists(macow_dir):
    os.mkdir(macow_dir)
if not os.path.exists(macow_data_dir):
    os.mkdir(macow_data_dir)
if not os.path.exists(macow_profiles_dir):
    os.mkdir(macow_profiles_dir)

os.chdir(macow_dir)

for item in os.listdir(macow_profiles_dir): ## Clean Profiles directory by removing .log files
    if item.endswith(".log"):
            os.remove(os.path.join(macow_profiles_dir, item)) 

## CODE ##

class c():

    def green(string):
        return Co.GREEN + string + S.RESET_ALL

    def red(string):
        return Co.RED + string + S.RESET_ALL

    def bold(string):
        return S.BRIGHT + Co.WHITE + string + S.RESET_ALL

    def err(string):
        return Co.RED + "[!] " + S.RESET_ALL + string

def mytime(): #Converts supplied time into seconds
    if args.M:
        minutes = int(args.M)
        mytime = minutes*60
    elif args.H:
        hours = int(args.H)
        mytime = hours*3600
    elif args.D:
        days = int(args.D)
        mytime = days*86400
    return mytime

def log_init():
    def items(amount):
        a = 0
        for i in range(len(amount)):
            a = a + 1
            yield a

    os.chdir(macow_profiles_dir)
    ls = os.listdir()
    b = list(items(ls))

    global load
    right_input = ['E','e','N', 'n']

    while True:
        load = input('Load an existing profile or create a new one ? (Existing[E]/New[N]) :')
        if load in right_input:
            break
        elif load not in right_input:
            print("Didn't get that...")

    if load == 'E' or load == 'e':
        if not ls:
            print('No profile to use, you should create one...')
            sys.exit()
        print('')
        print('Available profiles found :')
        print('')

        for x in range(0,len(ls)):
            c = str(b[x]) + ') ' + str(ls[x])
            print(c)

        print('')
        global filename
        while True:
            try:
                filename = int(input('Profile to load :'))
                choice = filename - 1
                filename = str(ls[filename - 1])
                break
            except (ValueError,IndexError):
                print("Didn't get that...")

        Connect_Log.log()
    elif load == 'N' or load == 'n':
        Connect.init()
        Connect_Log.log()

def timer(secs):
    try:
        nice_print = 'MAC ' + c.green(Mac.current()) + ' || Time '
        # range from seconds to zero backwards
        for x in range(secs, -1, -1):
            time.sleep(1)
            print(nice_print + c.green(formatTime(x)), end='\r', flush=True)
    except KeyboardInterrupt:
        pass      

def timer_no_log(secs):
    try:
        nice_print = 'Network ' + Connect.status() + ' || MAC ' + c.green(Mac.current()) + ' || Session '
        # range from seconds to zero backwards
        for x in range(secs, -1, -1):
            time.sleep(1)
            print(nice_print + c.green(formatTime(x)), end='\r', flush=True)
    except KeyboardInterrupt:
        pass 

def timer_log(secs):
    try:
        nice_print = 'Network ' + Connect.status() + ' || Login ' + Connect.login() + ' || MAC ' + c.green(Mac.current()) + ' || Session ' 
        # range from seconds to zero backwards
        for x in range(secs, -1, -1):
            time.sleep(1)
            print(nice_print + c.green(formatTime(x)), end='\r', flush=True)
    except KeyboardInterrupt:
        pass    

def formatTime(x):
    minutes, seconds = divmod(x, 60) 
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return "%02d:%02d:%02d:%02d" % (days, hours, minutes, seconds)

class Mac():
        
    def current():
        if sys.platform == "linux" or sys.platform == "darwin":
            mac = run('ifconfig ' + args.IFACE + " | grep ether | awk '{print$2}'", stdout=Capture()) 
            return mac.stdout.text.replace("\n","").upper()

    def anon():
        if sys.platform == "linux":
            if args.E:
                run('systemctl stop NetworkManager')
                run('ifconfig ' + args.IFACE + ' down')
                run('macchanger -A ' + args.IFACE + ' > /dev/null')
                run('ifconfig ' + args.IFACE + ' up')
                run('systemctl start NetworkManager')
        elif sys.platform == "darwin":
            if args.E:
                run('networksetup -setairportpower ' + args.IFACE + ' off')
                run('spoof-mac randomize ' + args.IFACE + ' > /dev/null')
                run('networksetup -setairportpower ' + args.IFACE + ' on')

    def randomize():
        if args.M or args.H or args.D:
            if args.M:
                minutes = int(args.M)
                mytime = minutes*60
            elif args.H:
                hours = int(args.H)
                mytime = hours*3600
            elif args.D:
                days = int(args.D)
                mytime = days*86400

            while True:
                Mac.anon()
                p = Process(target=timer, args=(mytime,))
                p.start()
                p.join() 
                p.terminate() 
        else:
            Mac.anon()
            print(args.IFACE + "'s MAC is now : " + c.green(Mac.current()))
        
    def specific():
        if sys.platform == "linux":
            run('ifconfig ' + args.IFACE + ' down')
            run('macchanger -m ' + args.S + ' ' + args.IFACE + '>/dev/null')
            run('ifconfig ' + args.IFACE + ' up')
        elif sys.platform == "darwin":
            run('spoof-mac set ' + args.S + ' ' + args.IFACE + '>/dev/null')
        print(args.IFACE + ' MAC is now : ' + c.green(Mac.current()))    
        
        
    def reset():
        if sys.platform == "linux":
            run('ifconfig ' + args.IFACE + ' down')
            run('macchanger -p ' + args.IFACE + ' >/dev/null')
            run('ifconfig ' + args.IFACE + ' up')
            print(args.IFACE + ' MAC is now back to : ' + c.green(Mac.current()))
        elif sys.platform == "darwin":
            run('spoof-mac reset ' + args.IFACE + ' >/dev/null')
        print(args.IFACE + ' MAC is now back to : ' + c.green(Mac.current()))

        
    def show():
        if sys.platform == "linux":
            default_mac = run('macchanger -p ' + args.IFACE + ' | grep "Permanent MAC" | awk ' + "'{print$3}'", stdout=Capture())
            default_MAC = default_mac.stdout.text.replace("\n","").upper()
        elif sys.platform == "darwin":
            default_mac = run('spoof-mac list' + ' | grep ' + args.IFACE + ' | awk ' + "'{print$9}'", stdout=Capture())
            default_MAC = default_mac.stdout.text.replace("\n","")
        print(args.IFACE + "'s permanent MAC is : " + c.green(default_MAC) + ', currently set to : ' + c.green(Mac.current()))

class Connect():

    def status(): # Ping google 10 times, return ✔ when success
        for x in range(10):
            try:
                file = urllib.request.urlopen('http://google.com')
                ping = c.green('✓')
                break
            except urllib.error.URLError:
                ping = c.red('✗')
                time.sleep(2)
        return ping

    def nmcli():
        essid_spaces = args.E.replace(" ", "\ ")

        if args.E and args.P:
            password_spaces = args.P.replace(" ", "\ ")
            run('nmcli con add type wifi con-name ' + essid_spaces + '-macow' + ' ssid ' + essid_spaces + ' ifname ' + args.IFACE + ' >/dev/null 2>&1')
            run('nmcli con mod ' + essid_spaces + '-macow' + ' wifi-sec.key-mgmt wpa-psk')
            run('nmcli con mod ' + essid_spaces + '-macow' + ' wifi-sec.psk ' + password_spaces)  
        else:
            run('nmcli con add type wifi con-name ' + essid_spaces + '-macow' + ' ssid ' + essid_spaces + ' ifname ' + args.IFACE + ' >/dev/null 2>&1')
        run('nmcli con up ' + essid_spaces + '-macow' + ' >/dev/null 2>&1')
                
    def nmcli_connect_log():
        essid_spaces = args.E.replace(" ", "\ ")
        run('nmcli con up ' + essid_spaces + '-macow' + ' >/dev/null 2>&1')

    def nmcli_randomize_switch(on):
        if on == 'on':
            run('cp /etc/NetworkManager/NetworkManager.conf ' + macow_data_dir + 'NetworkManager.conf.bak')
            run('rm /etc/NetworkManager/NetworkManager.conf')
            run('touch /etc/NetworkManager/NetworkManager.conf')

            with open("/etc/NetworkManager/NetworkManager.conf", "a") as f:
                f.write("\n")
                f.write("[device]\n")
                f.write("wifi.scan-rand-mac-address=no\n")
                f.write("[connection]\n")
                f.write("ethernet.cloned-mac-address=preserve\n")
                f.write("wifi.cloned-mac-address=preserve\n")
            run('systemctl restart NetworkManager')
            global nm_modified
            nm_modified = True
        else:
            run('rm /etc/NetworkManager/NetworkManager.conf')
            run('cp ' + macow_data_dir + 'NetworkManager.conf.bak /etc/NetworkManager/NetworkManager.conf')
            run('systemctl restart NetworkManager')

    def networksetup():
        essid_spaces = args.E.replace(" ", "\ ")

        if args.E and args.P:
            password_spaces = args.P.replace(" ", "\ ")
            run('networksetup -setairportnetwork ' + args.IFACE + ' ' + essid_spaces + ' ' + password_spaces + ' >/dev/null 2>&1')  
        else:
            run('networksetup -setairportnetwork ' + args.IFACE + ' ' + essid_spaces + ' >/dev/null 2>&1')

    def networksetup_connect_log():
        essid_spaces = args.E.replace(" ", "\ ")

        if args.E and args.P:
            password_spaces = args.P.replace(" ", "\ ")
            run('networksetup -setairportnetwork ' + args.IFACE + ' ' + essid_spaces + ' ' + password_spaces + ' >/dev/null 2>&1')
        else:
            run('networksetup -setairportnetwork ' + args.IFACE + ' ' + essid_spaces + ' >/dev/null 2>&1')

    def login():
        r3 = run('python3 ' + macow_profiles_dir + filename + ' >/dev/null 2>&1').returncode ## launch chromedriver 
        if r3 == 0:
            return c.green('✓')
        else:
            return c.red('✗')

    def init():
        print('')
        if sys.platform == "linux":
            Connect.nmcli_randomize_switch('on')
            Mac.anon()
            Connect.nmcli()
        elif sys.platform == 'darwin':
            Mac.anon()
            Connect.networksetup()

        print("Steps to create a PJS test :")
        print('')
        print('-> Selenium IDE')
        print('-> File')
        print('-> Export test case as')
        print('-> Python2 / unnitest / Webdriver')
        print('-> Save it in /YourHomeFolder/MacowFolder/Profiles/')
        print('-> Close Firefox and Selenium IDE')
        print('')

        if sys.platform == "linux":
            run('firefox -chrome "chrome://selenium-ide/content" firefox >/dev/null 2>&1') ## Launch firefox and selenium IDE
        elif sys.platform == "darwin":
            os.chdir('/Applications/Firefox.app/Contents/MacOS/')
            run('./firefox -chrome "chrome://selenium-ide/content" firefox >/dev/null 2>&1')

        os.chdir(macow_profiles_dir)
        latest_file = run('ls -t | head -1', stdout=Capture()) ## Get latest file
        global filename
        filename = latest_file.stdout.text.replace("\n","")
        print("Launching PhantomJS with profile " + "'" + c.green(filename) + "'")
            
        def replace_line(file_name, line_num, text):
            lines = open(file_name, 'r').readlines()
            lines[line_num + -1] = text + '\n'
            out = open(file_name, 'w')
            out.writelines(lines)
            out.close()

        replace_line(filename, 9, '\n')
        replace_line(filename, 9, 'options = webdriver.ChromeOptions()')
        replace_line(filename, 10, 'options.add_argument("headless")')
        replace_line(filename, 13, '        self.driver = webdriver.Chrome(chrome_options=options)')

class Connect_Log():
    
    def log():
        print('')
        ran_once = False
        if sys.platform == "linux":
            Connect.nmcli_randomize_switch('on')
        while True:
            if ran_once == False:
                if sys.platform == 'linux':
                    Mac.anon()
                    Connect.nmcli()
                elif sys.platform == "darwin":
                    Mac.anon()
                    Connect.networksetup()

                p = Process(target=timer_log, args=(mytime()-3,)) # get a new session 3 sec before countdown end
                p.start()
                p.join()
                p.terminate()
                ran_once = True

            elif ran_once == True:
                if sys.platform == 'linux':
                    Mac.anon()
                    Connect.nmcli_connect_log()
                elif sys.platform == 'darwin':
                    Mac.anon()
                    Connect.networksetup_connect_log()

                p = Process(target=timer_log, args=(mytime()-3,)) # get a new session 3 sec before countdown end
                p.start()
                p.join() 
                p.terminate()


    def no_log():
        print('')
        ran_once = False
        if sys.platform == "linux":
            Connect.nmcli_randomize_switch('on')
        while True:
            if ran_once == False:
                if sys.platform == 'linux':
                    Mac.anon()
                    Connect.nmcli()
                elif sys.platform == 'darwin':
                    Mac.anon()
                    Connect.networksetup()

                p = Process(target=timer_no_log, args=(mytime()-3,)) # get a new session 3 sec before countdown end
                p.start()
                p.join() 
                p.terminate()
                ran_once = True

            elif ran_once == True:
                if sys.platform == 'linux':
                    Mac.anon()
                    Connect.nmcli_connect_log()
                elif sys.platform == 'darwin':
                    Mac.anon()
                    Connect.networksetup_connect_log()

                p = Process(target=timer_no_log, args=(mytime()-3,)) # get a new session 3 sec before countdown end
                p.start()
                p.join() 
                p.terminate()

def exit():
    def con_restore():
        Mac.reset()
        print('Restoring connection...')
        if sys.platform == 'linux':
            run('systemctl restart NetworkManager')
        elif sys.platform == 'darwin':
            run('networksetup -setairportpower ' + args.IFACE + ' off')
            time.sleep(1)
            run('networksetup -setairportpower ' + args.IFACE + ' on')
        time.sleep(5)
        sys.exit()

    if args.E and args.LOG:
        if load == 'E' or load == 'e':
            print('')
            con_restore()
                
        elif load == 'N' or load == 'n':
            print('')
            while True:
                save = input('Save the profile named ' + "'" + c.green(filename) + "'" + ' (Y/N) :')
                if save in choices_yes:
                    print('Keeping ' + "'" + c.green(filename) + "' ...")
                    con_restore()
                    break

                elif save in choices_nope:  
                    print('Removing ' + "'" + c.green(filename) + "' ...")
                    os.remove(macow_profiles_dir + filename)
                    con_restore()
                    break
                else:
                    print("Didn't get that...")

    elif args.E:
        if nm_modified ==  True:
            print('')
            Connect.nmcli_randomize_switch('off')
            con_restore()
        elif nm_modified == False:
            print('')
            con_restore()
    else:
        print('') 
        con_restore()
                  

def main():
    if args.R and args.IFACE:
        Mac.randomize()

    if args.S and args.IFACE:
        Mac.specific()

    if args.U and args.IFACE:
        Mac.reset()

    if args.SHOW and args.IFACE:
        Mac.show()

    if args.M and args.E and args.LOG and args.IFACE:
        log_init()
        Connect_Log.log()

    elif args.M and args.E and args.IFACE: 
        Connect_Log.no_log() 
    
    elif args.M and args.IFACE:
        Mac.randomize()

    if args.H and args.E and args.LOG and args.IFACE:
        log_init()

    elif args.H and args.E and args.IFACE:
        Connect.connect_log()

    elif args.H and args.IFACE:
        Mac.randomize()

    if args.D and args.E and args.LOG and args.IFACE:
        log_init()

    elif args.D and args.E and args.IFACE:
        Connect.connect_log()

    elif args.D and args.IFACE:
        Mac.randomize()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()