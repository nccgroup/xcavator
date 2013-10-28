#!/usr/bin/env python3.3


#str port               Service port
#str user               Username for the service
#str passwd             Password
#IPv4Address ip         Target IP
#SRE_Pattern regex      Compiled RegEx
#str target_path        Current working directory: project_name\{IP address}
#Namespace args         Optional arguments

def startProtocol(port, user, passwd, ip, regex, target_path, args):
    global mirror, verbose, timeout
    mirror = args.search
    verbose = args.verbose
    timeout = args.timeout
    print("Your code here")