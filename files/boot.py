#!/usr/bin/python
""" Prints an iPXE script to stdout to start a kickstart & more """
import syslog
import sys
import os
import socket
sys.stderr = sys.stdout
print "Content-Type: text/plain"
print

syslog.openlog("boot.py")
syslog.setlogmask(syslog.LOG_UPTO(syslog.LOG_INFO))

try:
    # from the name, e.g. c1-3.cloud.example.org take c1-3
    hostname = socket.gethostbyaddr(os.environ["REMOTE_ADDR"])[0].split(".")[0]
    syslog.syslog(syslog.LOG_DEBUG, "Got boot iPXE request from " + hostname)

    os.stat("/var/www/provision/reinstall/" + hostname)
    os.remove("/var/www/provision/reinstall/" + hostname)
    f = open("/var/www/provision/nodes/" + hostname + ".conf")

    syslog.syslog(syslog.LOG_INFO, "Reinstalling node " + hostname)
    nodesettings = {}
    for line in f.readlines():
      #for every line, e.g. "key=value", set nodesettings["key"]="value"
      #comment lines will throw an error, skip them
        try:
            nodesettings[line.split("=")[0]] = line.split("=", 1)[1].strip()
        except:
            pass

    f.close()
    print "#!ipxe"
    print "kernel " + nodesettings["kernel_url_path"] + "/vmlinuz ks=" + nodesettings["kickstart_url"] + " edd=off ksdevice=bootif kssendmac console=ttyS1,115200 console=tty0 initrd=initrd.img " + nodesettings.get("extra_kernel_params", "")
    print "initrd " + nodesettings["kernel_url_path"] + "/initrd.img"
    print "boot"

# Catch the exception when the reinstall file wasn't found
except OSError:
    print "#!ipxe"
    print "exit"
# Catch all other problems
except Exception as exc:
    print str(exc)
    syslog.syslog(syslog.LOG_ERR, str(exc))

syslog.closelog()
