#!/usr/bin/env python3.3
# Released as open source by NCC Group Plc - http://www.nccgroup.com/
# Developed by Nikos Laleas, nikos dot laleas at nccgroup dot com
# https://github.com/nccgroup/xcavator
# Released under AGPL. See LICENSE for more information

import os
import re
import ipaddress
import configparser
import sys
import time
import mmap
import argparse



#Add your own protocols to the list
protocols = ['ftp', 'smb', 'ftps']

#Also add the default port
default_port = ['21', '139', '990']

num_files = 0
conf = ''
timeout = 0
verbose = 0
mirror = True


def main():
    print("+"+58*"-"+"+")
    print("   _    _                              _                  ")
    print("  ( )  ( )                            ( )_                ")
    print("  `\\`\\/'/'   ___    _ _  _   _    _ _ | ,_)   _    _ __   ")
    print("    >  <   /'___) /'_` )( ) ( ) /'_` )| |   /'_`\\ ( '__)  ")
    print("   /'/\\`\\ ( (___ ( (_| || \\_/ |( (_| || |_ ( (_) )| |     ")
    print("  (_)  (_)`\\____)`\\__,_)`\\___/'`\\__,_)`\\__)`\\___/'(_)     ")
    print("\n"+"+"+58*"-"+"+"+"\n")

    args = parseArgs()
    if os.path.isfile(conf):
        print ('Using existing configuration...')
        read_conf(args)
    else:
        print ('Config not found. Creating new...')
        create_new_conf(args)

def parseArgs():
    global conf, timeout, verbose, mirror
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type = str, default = 'xcavator.conf', help = 'Config file (Default: xcavator.conf)')
    parser.add_argument('-t', '--timeout', type = float, default = 2, help = 'Timeout in seconds (Default: 2s)')
    parser.add_argument('-s', '--search', default = True, action = 'store_false', help = 'Search mode. Searches recursively for filenames matching RegEx instead of downloading everything (Default: downloads everything and scans for strings)')
    parser.add_argument('-v', '--verbose', default = 0, action = 'count', help = 'Verbosity level. More "v"s, more detail. (Default: Prints basic info)')
    args = parser.parse_args()
    conf = args.config
    timeout = args.timeout
    verbose = args.verbose
    mirror = args.search
    return args

def create_new_conf(args):
    prot = input('Protocol (e.g. ftp): ')

    while prot.lower() not in protocols:
        prot = input('Invalid protocol. Try again: ')
        
    port = input('Port [' + default_port[protocols.index(prot)] + ']: ')
    if port is '': port = default_port[protocols.index(prot)]
    user = input('Username [anonymous]: ')
    passwd = input('Password [anonymous]: ')
    if user is '':
        user = 'anonymous'
        if passwd is '': passwd = 'anonymous'
    ip_range = input('IP range: ')
    ip_range_exp = validate_ip_range(ip_range)
    while True:
        if ip_range_exp:
            break
        else:
            ip_range = input('Try again: ')
            ip_range_exp = validate_ip_range(ip_range)
    regex = input('Regex: ')
    compregex= ""
    while True:
        try:
            compregex = re.compile(regex)
            break
        except re.error as err:
            print('RegEx error: %s' %err)
            regex = input('Try again: ')
    parser = configparser.ConfigParser()
    parser[prot.upper()] = {'PORT': port,
                            'User': user,
                            'Pass': passwd,
                            'Range': ip_range,
                            'RegEx': regex}
    
    with open(conf, 'w') as configfile:
        parser.write(configfile)
    process_request(prot.lower(), port, user, passwd, ip_range_exp, compregex, args)



def read_conf(args):
    parser = configparser.ConfigParser()
    parser.read(conf)
    sections = parser.sections()
    prot = sections[0]
    if prot.lower() not in protocols:
        print ('Protocol not supported. Edit the configuration or delete it to create a new one.')
        sys.exit()
    port = parser[prot]['port']
    if port is '':
        print ('Port not specified. Using default.')
        port = default_port[protocols.index(prot)]
    user = parser[prot]['user']
    passwd = parser[prot]['pass']
    if user is '':
        user = 'anonymous'
        if passwd is '':
            passwd = 'anonymous'
    ip_range = parser[prot] ['range']
    ip_range = validate_ip_range(ip_range)
    if not ip_range:
        print ('IP address range not valid. Edit the configuration or delete it to create a new one.')
        sys.exit()
    regex = parser[prot]['regex']
    try:
        regex = re.compile(regex)
    except re.error as err:
        print('RegEx error: %s' %err)
        sys.exit()
    process_request(prot.lower(), port, user, passwd, ip_range, regex, args)



def validate_ip_range(iprange):
    iprange = iprange.replace(" ","")
    iprange = iprange.split(',')
    ip_list=[]

    for ip in iprange:
        try:
            i=ipaddress.ip_address(ip)
            if i:
                ip_list.append(i)
        except ValueError:
            try:
                i=ipaddress.ip_network(ip)
                if i:
                    for x in i.hosts():
                        ip_list.append(x)
            except ValueError:
                if ip.find('-')==-1:
                    print('Invalid range or IP address -> ', ip)
                    return None
                else:
                    temp=ip.split('-')
                    for t in temp:
                        try:
                            ipaddress.ip_address(t)
                        except ValueError:
                            print('Invalid syntax -> ', t)
                            return None
                    if ipaddress.ip_address(temp[0])>ipaddress.ip_address(temp[1]) :
                        print('Invalid syntax -> ' + temp[0] + ' is higher than ' + temp[1])
                        return None
                    else:
                        x=ipaddress.ip_address(temp[0])
                        while x <= ipaddress.ip_address(temp[1]):
                            ip_list.append(x)
                            x+=1
    return ip_list



def process_request(prot, port, user, passwd, ip_range, regex, args):
    try:
        projPath = 'scan_%4d-%02d-%02d_%02d.%02d.%02d' % time.localtime()[0:6]
        print('Creating project directory...: %s' % projPath)
        makedir(projPath)
        projPath=os.path.join(os.getcwd(), projPath)
        prot = prot+'_proto'
        temp = __import__('protocols', fromlist = [prot])
        prot = getattr(temp, prot)
        for ip in ip_range:
            target_path=os.path.join(projPath, str(ip))
            makedir(target_path)
            os.chdir(target_path)
            prot.startProtocol(port, user, passwd, ip, regex, target_path, args)
            #globals()[prot + '_func'](port, user, passwd, ip, regex, projPath)
            try:
                os.chdir(projPath)
                os.rmdir(target_path)
            except OSError as err:
                pass
        if mirror: scanFiles(regex, projPath)
    except KeyError:
        print ('Method %s not implemented' % prot)
        sys.exit()


def scanFiles(regex, projPath):
    print('Scanning files...')
    regex = str.encode(regex.pattern)
    for curdir, dirs, files in os.walk(projPath):
        for file in files:
            try:
                filepath = os.path.join(curdir, file)
                if verbose > 2: print('Scanning file: %s' % filepath)
                size = os.stat(filepath).st_size
                f = open(filepath)
                data = mmap.mmap(f.fileno(), size, access=mmap.ACCESS_READ)
                f.close()
                newfile = ''
                counter = 1
                for m in re.finditer(regex, data):
                    if newfile is not file:
                        print('\n'+70*'='+'\nFile: %s' % filepath)
                        print(70*'=')
                    newfile = file
                    print('%d. Match: %s at offset: 0x%0.8x' % (counter ,m.group(0), m.start()))
                    counter += 1
            except ValueError as err:
               if verbose > 2: print('Error: %s' % err)
               continue
            if counter > 1: print(70*'-'+'\n')
    print("Done.")


def makedir(path):
    if os.path.isdir(path):
        return
    dirname = os.path.dirname(path)
    if dirname: makedir(dirname)
    os.mkdir(path, 0o777)


def convert_bytes(bytes):
    bytes = float(bytes)
    if bytes >= 1099511627776:
        terabytes = bytes / 1099511627776
        size = '%.2fTB' % terabytes
    elif bytes >= 1073741824:
        gigabytes = bytes / 1073741824
        size = '%.2fGB' % gigabytes
    elif bytes >= 1048576:
        megabytes = bytes / 1048576
        size = '%.2fMB' % megabytes
    elif bytes >= 1024:
        kilobytes = bytes / 1024
        size = '%.2fKB' % kilobytes
    else:
        size = '%.2fb' % bytes
    return size

if __name__ == '__main__':
    main()
