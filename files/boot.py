#!/usr/bin/python
""" Prints an iPXE script to stdout to start a kickstart & more """
from __future__ import print_function
import sys
import os
import socket
import syslog
import json

sys.stderr = sys.stdout
print("Content-Type: text/plain")
print()

PXE_HEADER = "#!ipxe"
if "gPXE" in os.environ["HTTP_USER_AGENT"]:
    PXE_HEADER = "#!gpxe"


def pxe_abort():
    """Abort the PXE boot, continue with the next boot device in the BIOS boot order"""
    print(PXE_HEADER)
    print("exit")
    sys.exit(0)

syslog.openlog("boot.py")
syslog.setlogmask(syslog.LOG_UPTO(syslog.LOG_INFO))

# from the name, e.g. c1-3.cloud.example.org take c1-3 and put it in HOSTNAME
try:
    FQDN = socket.gethostbyaddr(os.environ["REMOTE_ADDR"])[0]
    HOSTNAME = FQDN.split(".")[0]
except Exception as e_xcep:
    syslog.syslog(
        syslog.LOG_ERR,
        str(e_xcep) + " HOSTNAME wasn't found in /var/www/provision/nodes/pxe_nodes.json",
    )
    pxe_abort()

syslog.syslog(syslog.LOG_DEBUG, "Got boot iPXE request from " + HOSTNAME + "(" + FQDN + ")")

####### Memtest
STARTED = False
# When a hypervisor restarts without a reinstall/memtest it is expected that the tries fails.
try:
    # for convenience admins on the web server that houses boot.py
    #  needs to create a file called HOSTNAME == short hostname and not FQDN
    os.stat("/var/www/provision/memtest86/" + HOSTNAME)
    os.remove("/var/www/provision/memtest86/" + HOSTNAME)

    #  pxe_nodes.json however has whatever is in the ansible inventory which might be the
    #  inconveniently long FQDN
    with open("/var/www/provision/nodes/pxe_nodes.json") as f:
        j = json.load(f)
    NODESETTINGS = j[FQDN]

    syslog.syslog(syslog.LOG_INFO, "Memtesting node " + HOSTNAME)

    # http://forum.ipxe.org/showthread.php?tid=7937&highlight=memtest
    # https://git.ipxe.org/people/mcb30/memtest.git/commitdiff/fac651cb5f52f4dc2435c5c11ada06215a5b9ec9
    # there is no "pxe" referenced in memtest86+ 7.5 source code (found inside the iso)
    print(PXE_HEADER)
    print("kernel " + NODESETTINGS["memtest86_0_path"])
    print("boot")
    STARTED = True

# Catch the exception when the memtest file wasn't found
except OSError:
    pass
# Catch all other problems
except Exception as exc:
    # print(str(exc))
    syslog.syslog(syslog.LOG_ERR, "Error: " + str(exc))

######## Reinstall

if not STARTED:
    try:
        os.stat("/var/www/provision/reinstall/" + HOSTNAME)
        os.remove("/var/www/provision/reinstall/" + HOSTNAME)

        with open("/var/www/provision/nodes/pxe_nodes.json") as f:
            j = json.load(f)
        NODESETTINGS = j[FQDN]

        # default sets up both serial and console
        SERIALPORT = "console=ttyS1,115200 console=tty0"
        EXTRA_KERNEL_PARAMS = ""
        if "serialport" in NODESETTINGS:
            SERIALPORT = NODESETTINGS["serialport"]
        if "extra_kernel_params" in NODESETTINGS:
            EXTRA_KERNEL_PARAMS = NODESETTINGS["extra_kernel_params"]

        syslog.syslog(syslog.LOG_INFO, "Reinstalling node " + HOSTNAME)
        print(PXE_HEADER)
        print(
            "kernel "
            + NODESETTINGS["kernel_url_path"]
            + "/vmlinuz ks="
            + NODESETTINGS["kickstart_url"]
            + " edd=off ksdevice=bootif kssendmac "
            + SERIALPORT
            + "initrd=initrd.img "
            + EXTRA_KERNEL_PARAMS
        )
        print("initrd " + NODESETTINGS["kernel_url_path"] + "/initrd.img")
        print("boot")

    # Catch the exception when the any memtest/reinstall file wasn't found
    except OSError:
        pxe_abort()
    # Catch all other problems
    except Exception as exc:
        print(str(exc))
        syslog.syslog(syslog.LOG_ERR, "Error for " + HOSTNAME + ": " + str(exc))

syslog.closelog()
