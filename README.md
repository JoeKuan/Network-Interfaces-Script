# Network-Interfaces-Script (Ver 1.2)

Read and update awk scripts for Ubuntu /etc/network/interfaces file.

**readInterfaces.awk** -- parse and output interface configuration
**changeInterface.awk** -- modify interfaces file

## Parse Interfaces Script
Complete re-implement both scripts with much simpler logic, shorter code and pack with more flexible features. It now allows you to add/modify/delete interfaces, as well as add/modify/delete any settings within an interface. These scripts are tested with testChangeInterface.py python script.

### Update Interfaces Script (changeInterface.awk)
Here is the standard usage for changeInterface.awk:

```
awk -f changeInterface.awk <interfaces file> <device=ethX> 
     <mode=(dhcp|static|manual)> [action=add|remove] 
     [address=<ip addr> netmask=<ip addr> <name=value> ...]
```

* `device=ethX` - target network interface to configure
* `mode=(dhcp|static|manual)` - type of network interface to configure. This argument is not required when `action` is `remove`
* `action=(add|remove)` - optional argument. Add or remove an interface entry. If this argument is not specified, it assumes `modify` operation
* `name=value` - configuration for a network interface. The script doesn't limit what settings as long as in name and value syntax. For example:
   * `network=192.168.0.0` - modify (if already exists) or add the network setting
   * `network=` - specify without value means to remove the network setting if already exists
   * `'dns-nameservers=192.168.200.5 10.0.10.1'` - for settings with multiple values, enter with quote around it. Or you can use `dns=192.168.200.5` as short form.

#### Usage Examples:
**Configure network device _eth0_ to DHCP mode**
```
awk -f changeInterfaces.awk /etc/network/interfaces device=eth0 mode=dhcp
```
**Add a network device _p3p1_ with static settings**
```
awk -f changeInterfaces.awk /etc/network/interfaces device=p3p1 action=add mode=static address=192.168.202.1 netmask=255.255.255.0 gateway=192.168.202.254
```
If _p3p1_ already exists and configured as DHCP, it will automatically modify to static interface with all the input settings.

If _p3p1_ already exists and configured as static, it will overwrite the existing field or add the field if it is new.

**Delete an interface entry**
```
awk -f changeInterfaces.awk /etc/network/interfaces device=eth1 action=remove 
```

**Remove `network` & `broadcast` fields and add (or modify if exists) `dns-nameservers` & `foo` fields**
```
awk -f changeInterfaces.awk /etc/network/interfaces device=eth1 mode=static network= broadcast= foo=bar 'dns-nameservers=10.0.10.1 192.168.200.5 192.168.202.254'
```
### Read Interfaces Script (readInterfaces.awk)
Here is the standard usage for readInterface.awk:

```
awk -f readInterfaces.awk <interfaces file> <device=ethX> [output=all]
```
* `output=all` - print out the full settings for an interface. Without this option, the script will just print out the basic address config in : `ipaddr netmask gateway` (separated with a single white space). With this option, all the settings are displayed, e.g.
```
192.168.0.10 255.255.255.0 192.168.0.1
bridge_maxage 12
broadcast 192.168.0.255
network 192.168.0.0
bridge_stp off
bridge_fd 9
bridge_ports eth0
bridge_hello 2
```
 
