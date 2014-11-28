# Network-Interfaces-Script

Read and update awk scripts for Ubuntu /etc/network/interfaces file.

**readInterfaces.awk** -- parse and output interface configuration
**changeInterface.awk** -- modify interfaces file

## Parse Interfaces Script

_awk -f readInterfaces.awk <interfaces file> <device=ethX>_

For usage sample and more information, see [this blog](1).

## Update Interfaces Script

_awf -f changeInterface.awk <interfaces file> <device=ethX> <name=value>_

For usage sample and more information, see [this blog](2).

[1]: http://joekuan.wordpress.com/2009/11/01/awk-scripts-for-reading-and-editing-ubuntu-etcnetworkinterfaces-file-part-12/
[2]: http://joekuan.wordpress.com/2009/11/01/awk-scripts-for-reading-and-editing-ubuntu-etcnetworkinterfaces-file-part-22/
