#!/usr/bin/env python3.3
# Released as open source by NCC Group Plc - http://www.nccgroup.com/
# Developed by Nikos Laleas, nikos dot laleas at nccgroup dot com
# https://github.com/nccgroup/xcavator
# Released under AGPL. See LICENSE for more information

import os
from sys import stdout
from xcavator import convert_bytes
from smb import smb_structs
from smb.SMBConnection import SMBConnection


def startProtocol(port, user, passwd, ip, regex, target_path, args):
    global mirror, verbose, timeout
    mirror = args.search
    verbose = args.verbose
    timeout = args.timeout
    serverName = '*'
    conn = []
    direct = True
    if port != '445':
        serverName = input("SMB over TCP is used by default on port 445.\nIf you prefer NetBIOS instead, you need to provide the NetBIOS name of the remote machine: ")
        direct = False
    try:
        conn = SMBConnection(user, passwd, 'noone', serverName, use_ntlm_v2 = True, is_direct_tcp = direct)
        stdout.write("Trying SMB server: %s......" % str(ip))
        stdout.flush()
        conn.connect(str(ip), int(port), timeout = timeout)
        print("[Connected]")
        shares(target_path, conn, regex)
        conn.close()
    except OSError as err:
        print("[No connection]")
        if verbose > 0: print(err.message)
        conn.close()
        pass


def makedir(path):
    if os.path.isdir(path):
        return
    os.mkdir(path, 0o777)


def shares(targetPath, conn, regex):
    global num_files, size
    shareList = conn.listShares()
    num_files = 0
    size = 0
    if verbose == 0: print("Downloading files...")
    for r in shareList:
        if targetPath and not os.path.isdir(os.path.join(targetPath, r.name)):
            try:
                makedir(os.path.join(targetPath, r.name))
            except os.error as err:
                if verbose > 0: print(err)
                return

        downloadSMBFiles("\\", os.path.join(targetPath,r.name), conn, regex, r.name)
    print('%i files (%s) downloaded. Closing connection...' % (num_files, convert_bytes(size)))


def downloadSMBFiles(smbpath, projPath, conn, regex, share):
    global num_files, size
    cwd = ""
    if smbpath[:1] is "\\": cwd = (smbpath[1:]) #trim first \
    cwd = os.path.join(projPath,cwd)
    if cwd and not os.path.isdir(cwd):
        try:
            makedir(cwd)
        except os.error as err:
            if verbose > 0: print(err)
            return


    subdirs = []
    try:
        listing = conn.listPath(share, smbpath)
        for l in listing:
            filename = l.filename
            if l.isDirectory:
                if filename is ".": continue
                if filename == "..": continue #Using 'is' didn't work
                subdirs.append(filename)
                continue
            else:
                relativeRemotePath = os.path.join(smbpath, l.filename)
                relativeLocalPath = os.path.join(share, relativeRemotePath[1:])
                tempname = relativeLocalPath+'.tmp'
                try:
                    os.unlink(tempname)
                except os.error:
                    pass
                try:
                    fp = open(tempname, 'wb')
                except IOError as err:
                    if verbose > 0: print ("Can't create %r: %s" % (tempname, err))
                    continue
                try:
                    if not mirror:
                        if verbose > 2: print('Checking file: %r' % relativeRemotePath)
                        if regex.match(filename):
                            print('***Found match...***')
                            if verbose > 0: print("Downloading file: %s.....[%s]" % (relativeRemotePath, convert_bytes(l.file_size)))
                            file_attributes, filesize = conn.retrieveFile(share, relativeRemotePath, fp)
                            fp.close()
                            size += filesize
                            num_files+=1
                        else:
                            if verbose > 2: print('Not matched...')
                            fp.close()
                            os.remove(tempname)
                    else:
                        if verbose > 1: print("Downloading file: %s.....[%s]" % (relativeRemotePath, convert_bytes(l.file_size)))
                        try:
                            file_attributes, filesize = conn.retrieveFile(share, relativeRemotePath, fp)
                            size += filesize
                            fp.close()
                        except smb_structs.OperationFailure as err:
                            if verbose > 1: print(err.message)
                            fp.close()
                            os.remove(tempname)
                            continue
                        num_files+=1
                except OSError as err:
                    if verbose > 0: print ('%s: %s' %(relativeRemotePath, err))
                    fp.close()
                    os.remove(tempname)
                    continue
                try:
                    os.unlink(relativeRemotePath)
                except os.error:
                    pass
                try:
                    os.rename(tempname, relativeLocalPath)
                except os.error:
                    continue

        for subdir in subdirs:
            localsub = os.path.join(cwd, subdir)
            newdest = smbpath+subdir+"\\"
            if verbose > 2: print('Changing current directory to: %s' % (share+newdest))
            downloadSMBFiles(newdest, projPath, conn, regex, share)

            #Delete empty directories
            try: os.rmdir(localsub)
            except OSError: pass

        return num_files

    except smb_structs.OperationFailure as err:
        #print(err)
        return


