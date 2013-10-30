#!/usr/bin/env python3.3
# Released as open source by NCC Group Plc - http://www.nccgroup.com/
# Developed by Nikos Laleas, nikos dot laleas at nccgroup dot com
# https://github.com/nccgroup/xcavator
# Released under AGPL. See LICENSE for more information

from ftplib import FTP_TLS
from xcavator import convert_bytes
import ftplib
import os


def startProtocol(port, user, passwd, ip, regex, target_path, args):
    global num_files, size, mirror, verbose, timeout
    num_files = 0
    size = 0
    mirror = args.search
    verbose = args.verbose
    timeout = args.timeout
    try:
        print(70*'#')
        print('Trying FTPS server: %s:%s' %(ip, port))
        host = FTP_TLS(str(ip), timeout = timeout)
        host.login(user, passwd)
        host.prot_p()
        print('Connected... Downloading files...\n')
        files = downloadFTPFiles(target_path, host, regex)
        print('%i files (%s) downloaded... Closing connection...' % (files, convert_bytes(size)))
        host.close()
    except ftplib.all_errors as err:
        print (err)


def makedir(path):
    if os.path.isdir(path):
        return
    dirname = os.path.dirname(path)
    if dirname: makedir(dirname)
    os.mkdir(path, 0o777)


def downloadFTPFiles(destination, host, regex):
    global num_files, size
    pwd = host.pwd()
    if destination and not os.path.isdir(destination):
        try:
            makedir(destination)
        except os.error as err:
            if verbose > 0: print(err)
            return
    subdirs = []
    listing = []
    host.retrlines('LIST', listing.append)
    for line in listing:
        prop = line.split(None, 8)
        if len(prop) < 6: continue
        filename = prop[-1].lstrip()
        #is symlink?
        if (prop[0][0]) is 'l': continue
        if filename is ('.' or '..'): continue
        #is directory?
        if (prop[0][0]) is 'd':
            subdirs.append(filename)
            continue
        fullname = os.path.join(destination, filename)
        tempname = os.path.join(destination, filename+'.tmp')
        try:
            os.unlink(tempname)
        except os.error:
            pass
        try:
            fp = open(tempname, 'wb')
        except IOError as err:
            if verbose > 0: print ("Can't create %r: %s" % (tempname, err))
            continue
        fullpath=''
        if pwd is not '/': fullpath = '%s/%s' %(pwd, filename)
        else: fullpath = '/%s' % filename
        try:
            if not mirror:
                if verbose > 2: print('Checking file: %r' % fullpath)
                if regex.match(filename):
                    if verbose > 2: print('***Found match...')
                    filesize = host.size(filename)
                    if verbose > 1: print('Downloading file: %s.....[%s]' % (fullpath, convert_bytes(filesize)))
                    host.retrbinary('RETR ' + filename, fp.write, 8*1024)
                    size += filesize
                    num_files+=1
                else:
                    if verbose > 2: print('No match...')
                    fp.close()
                    os.remove(tempname)
            else:
                filesize = host.size(filename)
                if verbose > 1: print('Downloading file: %s.....[%s]' % (fullpath, convert_bytes(filesize)))
                host.retrbinary('RETR ' + filename, fp.write, 8*1024)
                size += filesize
                num_files+=1
        except ftplib.error_perm as err:
            if verbose > 1: print ('%s: %s' %(fullpath, err))
            fp.close()
            os.remove(tempname)
            continue
        fp.close()
        try:
            os.unlink(fullname)
        except os.error:
            pass
        try:
            os.rename(tempname, fullname)
        except os.error:
            continue

    for subdir in subdirs:
        localsub = os.path.join(destination, subdir)
        pwd = host.pwd()
        try:
            if verbose > 2: print('Changing current directory to: %r' % (pwd+subdir))
            host.cwd(subdir)
        except ftplib.error_perm as err:
            if verbose > 0: print('%s\n%s' %(subdir, err))
            continue
        else:
            downloadFTPFiles(localsub, host, regex)
            host.cwd('..')
        if host.pwd() != pwd:
            break
        #Delete empty directories
        try: os.rmdir(localsub)
        except OSError: pass
    return num_files
