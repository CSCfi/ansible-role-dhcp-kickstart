Spacewalk proxy  Ansible role
=============================

This is an Ansible role for configuring PXE/iPXE provisioning, either by
pointing it to en external kickstart source (e.g. Spacewalk) or by provisioning
the kickstart file itself.

This role sets up the following:
 - DHCP iPXE chainbooting
  - DHCP configs for nodes that should be provisioned
  - Generic static DHCP allocations
 - XINETD TFTP server for the chainbooting
 - Apache HTTP server
  - Python script under cgi-bin for handling reprovisioning logic
  - A provisioning directory for provisioning data
  - Optionally kickstart files for the desired groups

Prerequisites
-------------

This role assumes that a ISC DHCP server has been set up by another role.

Usage
-----

This role works by setting up pxe booting based on groups. It configures PXE
booting for all hosts in the desired group. By default it's "dhcp_pxe_nodes",
but it can be defined (check defaults/main.yml)

Each host needs the follwing variables in its scope.

Mandatory:
 - mac_address
 - ip_address
 - dhcp_server_ip
 - kickstart_url
 - kernel_url_path (path where kickstart kernel and initrd can be found)

Optional:
 - extra_kernel_params (for the kickstart)
 - dhcp_domain
 - memtest86_0_path (for pointing to a memtest.0 PXE NBP)

The nodes which only need to be set up for DHCP need to be in the
(by default) "dhcp_only_nodes"  group. These nodes need the following 
variables.

 - mac_address
 - ip_address

The role also configures a per-group kickstart file for each group which has the
"os_disks" variable in its scope. For this it uses the following variables from
the groups context.

Mandatory:
 - install_repo
 - additional_repos
 - root_password_hash
 - os_disks (in the kickstart format, e.g. "sda,sdb")
 - kickstart_partitions (list of kickstart partition instructions)
 - root_keys (public ssh keys to deploy for root)

Optional:
 - kernel_numa_param(can be set to off)


Caveats
-------

The role doesn't allow much in the way of kickstart parametrization. It might
make some assumptions on the system state (e.g DHCP config).

The role by default does not install chrony in the kickstart, set variable

<pre>
dhcp_kickstart_install_chrony: True
</pre>

to keep chrony.
