#!/usr/bin/python
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
    # from the name, e.g. c1-3 take c1-3
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
    bootstrap = ""
    if "kickstart_url" in nodesettings:
        bootstrap = " ks=" + nodesettings["kickstart_url"] + " ksdevice=bootif kssendmac"
    elif "autoyast_url" in nodesettings:
        bootstrap = " autoyast=" + nodesettings["autoyast_url"] + " install=" + nodesettings["autoyast_install_url"]
    print "#!ipxe"
    print "kernel " + nodesettings["kernel_url_path"] + "/" + nodesettings.get("kernel_name", "vmlinuz") + bootstrap + " edd=off console=ttyS1,115200 console=tty0 initrd=" + nodesettings.get("initrd_name", "initrd.img") + " " + nodesettings.get("extra_kernel_params", "")
    print "initrd " + nodesettings["kernel_url_path"] + "/" + nodesettings.get("initrd_name", "initrd.img")
    print "boot"

# Catch the exception when the reinstall file wasn't found
except OSError:
    print "#!ipxe"
    print "exit"
# Catch all other problems
except Exception as e:
    print str(e)
    syslog.syslog(syslog.LOG_ERR, str(e))

syslog.closelog()
