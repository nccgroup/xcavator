xcavator
========
A network data locater using credentials obtained during penetration tests.

Xcavator is a tool that scans a range of IP addresses for services that host files (FTP, FTPS and SMB at the moment) and for
given credentials it will try to download everything it can and scan within the files for interesting strings.

Another mode is to download only those files that their filenames match a RegEx.

Developed by Nikos Laleas, nikos d0t laleas at nccgroup d0t com

Released under AGPL. See LICENSE for more information.

Prerequisites
-------------
Python 3.3 and [[https://pypi.python.org/pypi/pysmb | pysmb]]

Options
-------
All the necessary parameters are picked up from a config file witch is created and populated on the first run.

#####Config file example
<pre>
[SMB]
user = h4x0r
pass = 123456
regex = \bpassword\b
port = 445
range = 192.168.1.1-192.168.1.15, 10.10.10.0/24
</pre>

There are also additional optional arguments:

<pre>
  -h, --help                      show this help message and exit
  
  -c CONFIG, --config CONFIG      Config file (Default: xcavator.conf)
  
  -t TIMEOUT, --timeout TIMEOUT		Timeout in seconds (Default: 2s)
  
  -s, --search                    Search mode. Searches recursively for filenames
                                  matching RegEx instead of downloading everything
                                  (Default: downloads everything and scans for strings)
                                  
  -v, --verbose                   Verbosity level. More "v"s, more detail. (Default: Prints basic info)
</pre>

Adding new protocols
--------------------
In order to support new protocols you need to create a file named protocolname_proto.py in the 'protocols' directory. Have a look at 'sample_proto.py'.
Finally, edit the 'xcavator.py' and add the protocol name and the default port to the correspondent lists.