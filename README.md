PXEboot role for Ansible
========================

This is an Ansible role for configuring PXE/iPXE provisioning, either by
pointing it to an external install source or by provisioning a bootstrapping
file itself (kickstart or autoyast).

This role sets up the following:

 - Generates DHCP config files
  - iPXE chainbooting support
  - DHCP configs only for nodes that should be serviced
  - Generic static DHCP allocations
  - PXE provisioning can be enabled for desired hosts
 - XINETD TFTP server for the chainbooting
 - Apache HTTP server
  - Python script under cgi-bin for handling reprovisioning logic
  - A provisioning directory for provisioning data
 - Optionally generates kickstart or autoyast files for the desired hosts
 - Optionally populates /etc/hosts

Prerequisites
-------------

This role assumes that an ISC DHCP server has been set up by another role. The
role [ansible-role-dhcp_server][1] can be used. Combined they form a complete
iPXE provisioning environment.

[1]: https://github.com/SoneraCloud/ansible-role-dhcp_server

Usage
-----

This role is intended to be included in the host loop by delegating the role's
execution to a dedicated dhcp server. The hosts being serviced with DHCP and/or
PXE should be added to one umbrella group. The hosts can individually be
configured to use the services (or not) as long as the mandatory variables are
in the scope of the play. See the usage example on how to use this role.

To enable the PXE chainbooting services for a host set use_pxe to true. To only
provide static DHCP allocations you can set use_dhcp to true and leave use_pxe
as false.


Each host needs the following variables in its scope.

Mandatory:

 - mac_address
 - ip_address
 - dhcp_server_ip
 - use_dhcp (def: false)
 - use_pxe (def: false)
 - use_kickstart (def: true)
 - use_autoyast (def: false)

Optional (or mandatory):

 - kernel_url_path (url base where kernel and initrd can be found)
 - kernel_name (kernel filename, def: vmlinuz)
 - initrd_name (initrd filename, def: initrd.img)
 - extra_kernel_params (extra kernel cmdline parameters)
 - dhcp_domain (defaults to dhcp_common_domain from the [dhcp_server][1] role)
 - generate_hosts_file (populates /etc/hosts on the server, def: false)

The nodes which only need to be set up for DHCP only need the following 
variables.

 - mac_address
 - ip_address


When **use_kickstart** is enabled the following variables are used.

Mandatory:

 - install_repo
 - root_password_hash
 - os_disks (in the kickstart format, e.g. "sda,sdb")
 - kickstart_partitions (list of kickstart partition instructions)
 - root_keys (public ssh keys to deploy for root)

Optional:

 - kickstart_url
 - additional_repos (list of dicts: [name, url, options])
 - lang (def: en_US.UTF-8)
 - keyboard (def: fi-latin1)
 - timezone (def: Europe/Helsinki)
 - kickstart_packagesfile (def: templates/kickstart-packages.j2)
 - kickstart_postfiles (def: [templates/kickstart-post.j2])


When **use_autoyast** is enabled the following variables are used.

Mandatory:

 - autoyast_install_url
 - root_password_hash
 - autoyast_partitions (xml snippet of partition instructions)
 - root_keys (public ssh keys to deploy for root)

Optional:

 - autoyast_url
 - lang (def: en_US.UTF-8)
 - autoyast_keyboard (def: finnish)
 - timezone (def: Europe/Helsinki)

Caveats
-------

This role has only been tested on RHEL-derivatives (CentOS) and is suited to
boot up RHEL-derivatives (built-in kickstart support) or SUSE/SLES (built-in 
autoyast support). However, other OSs can also be booted by pointing the hosts
to a proper pxe install base. Works also with PXE booted KVM VMs.


Example
-------

Host variables

```yaml
dhcp_server_ip: 192.168.1.1
use_dhcp: true
use_pxe: true
kernel_url_path: "http://.../INSTALL/Centos/7/os/x86_64/images/pxeboot/"
install_repo: "http://.../INSTALL/Centos/7/os/x86_64/"
additional_repos:
  - { name: "EPEL", url: "http://.../epel/7/x86_64/", options: "--install" }
# Generate a random password that is discarded
pw: "{{ lookup('pipe', 'openssl rand -base64 28') }}"
pwsalt: "{{ lookup('pipe', 'openssl rand -hex 8') }}" 
# Don't set > 8 as hex output is twice the length and 16 chars is the maximum
# salt length on some library versions
root_password_hash: "{{ pw|password_hash('sha512', pwsalt) }}"
root_keys: 
  - "{{ some_deploy_key }}"
os_disks: "sda"
kickstart_partitions:
  - "part / --fstype=ext4 --asprimary --grow --size=4096 --ondisk=sda"
  - "part swap --asprimary --size=1024 --ondisk=sda"
```

Playbook example snippet

```yaml
# To include the generated host configs in ansible-role-dhcp_server set
# dhcp_common_parameters:
#   - 'include "/etc/dhcp/ipxe.conf"'
#   - 'include "/etc/dhcp/dhcpd_hosts.conf"'

- name: Install DHCP and PXE services
  hosts: pxebooter
  become: yes
  tasks:
    - include_role:
        name: ansible-role-dhcp_server
      vars:
        # Unset to be able to install dhcpd before the incl.files are generated
        dhcp_common_parameters: []

    - include_role:
        name: ansible-role-dhcp-kickstart

    - include_role:
        name: ansible-role-dhcp_server

# The host groups are listed under dhcp_hosts so we can loop through them here
# This portion can be called independently when new hosts are added
- name: Configure DHCP nodes
  hosts: dhcp_hosts
  gather_facts: false
  become: yes
  tasks:
    - name: Configure DHCP and PXE nodes
      delegate_to: "{{ dhcp_server_ip }}"
      include_role:
        name: ansible-role-dhcp-kickstart
        tasks_from: configure
      vars:
        dhcp_delegate_handlers_to: "{{ dhcp_server_ip }}"
```

To force (re)install for a host use a task like this

```yaml
- name: Create an empty file to toggle (re)install of image for host
  become: yes
  file: path="/var/www/provision/reinstall/{{ inventory_hostname_short }}" state=touch owner=apache group=apache mode=0444
  delegate_to: "{{ dhcp_server_ip }}"
```
