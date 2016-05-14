function writeStatic(addr, nw, nm, gw, dns, device) {

    if (length(addr)) 
        print "    address ", addr
    
    if (length(nw)) 
        print "    network ", nw 

    if (length(nm)) 
        print "    netmask ", nm

    if (length(gw)) 
        print "    gateway ", gw

    if (length(dns))
        print "    dns-nameservers ", dns

    if (length(br))
    {
        print "    bridge_ports", device
        print "    bridge_fd 0"
        print "    bridge_maxwait 0"
    }
}

function usage() {
        print "awk -f changeInterfaces.awk <interfaces file> dev=<eth device> \n" \
            "       [address=<ip addr>] [gateway=<ip addr>] [netmask=<ip addr>]\n" \
            "       [network=<ip addr>] [mode=add|dhcp|static|remove|manual] [dns=<ip addr [ip addr ...]>] [arg=debug]\n" \
            "       [bridge=<bridge device>]"
}

BEGIN { start = 0;
    dnsVal = "";
    
    if (ARGC < 3 || ARGC > 10) {
        usage();
        exit 1;
    }

    for (i = 2; i < ARGC; i++) {
        split(ARGV[i], pair, "=");
        if (pair[1] == "address")
            address = pair[2];
        else if (pair[1] == "gateway")
            gateway = pair[2];
        else if (pair[1] == "network")
            network = pair[2];
        else if (pair[1] == "netmask")
            netmask = pair[2];
        else if (pair[1] == "brigde")
            brigde = pair[2];
        else if (pair[1] == "dev")
            device = pair[2];
        else if (pair[1] == "dns") {
            if (!length(pair[2])) {
                dnsVal = "clear";
            } else {
                dnsVal = pair[2];
            }
        }
        else if (pair[1] == "arg" && pair[2] == "debug")
            debug = 1;
        else if (pair[1] == "mode" && pair[2] == "dhcp") 
            dhcp = 1;
        else if (pair[1] == "mode" && pair[2] == "static") 
            static = 1;
        else if (pair[1] == "mode" && pair[2] == "remove")
            remove = 1;
        else if (pair[1] == "mode" && pair[2] == "manual")
            manual = 1;
        else if (pair[1] == "mode" && pair[2] == "add")
            add = 1;
        else {
            usage();
            exit 1;
        }
    }

    # Sort out the logic of argument
    if (dhcp && (length(network) || length(gateway) || length(address) || length(netmask))) {
        print "Both DHCP and static properties are defined";
        usage();
        exit 1;
    }

} 

{
    # maybe remove auto if manual is selected??
    if ($1 == "auto" && remove ) {
        if($2 != device) 
            print;
        next;
    }

    # Look for iface line and if the interface comes with the device name
    # scan whether it is dhcp or static 
    if ($1 == "iface")  {


        # Ethernet name matches - switch the line scanning on
        if ($2 == device) {

            if (debug)
                print $0;
       
            # If remove is defined, switch on delete mode 
            if (remove) {
                definedRemove=1;
            }
 
            # It's a DHCP interface, if defined any static properties
            # change it to static
            if (match($0, / dhcp/)) {
                definedDhcp=1;
                # Change to static if defined properties
                if (length(address) || length (gateway) || 
                    length(netmask) || length (network) || static) {
                    print "iface", device, "inet static";
                    next;
                }
            }

            else if (match ($0, / manual/)) {
                definedManual=1;
                # Change to static if defined properties
                if (length(address) || length (gateway) || 
                    length(netmask) || length (network) || static) {
                    print "iface", device, "inet static";
                    next;
                }
                # Change to dhcp if defined
                if (dhcp) {
                    sub(/ manual/, " dhcp");
                    print $0;
                    next;
                }
            }

            # It's a static network interface
            else if (match ($0, / static/)) {
                definedStatic=1;
                # Change to dhcp if defined
                if (dhcp) {
                    sub(/ static/, " dhcp");
                    print $0;
                    next;
                }
                if (manual) {
                    sub(/ static/, " manual");
                    print $0;
                    next;
                }
            }

        } 
        # If it is other inteface line, switch it off
        else {
            if (definedStatic) {
                if (length(dnsVal) && dnsVal != "clear") {
                    if (debug) {
                        print "Detected new iface defined but dns hasn't been updated yet";
                    }
                    print "    dns-nameservers ", dnsVal;
                }
            }
            
            definedStatic = 0;
            definedDhcp = 0;
            definedRemove = 0;
            definedManual = 0;
        }

        if (!definedRemove) {
            print $0;
            next;
        }
    }

    # Reaches here - means non iface lines
    # Change the static content
    if (definedStatic) {

        # Already defined static, just changing the properties
        # Otherwise omit everything until the iface section is
        # finished
        if (!dhcp && !manual) {

            if (debug)
                print "static - ", $0, $1;
            
            if ($1 == "address" && length(address)) 
                print "    address ", address
       
            else if ($1 == "netmask" && length(netmask)) 
                print "    netmask ", netmask;
        
            else if ($1 == "gateway" && length(gateway))
                print "    gateway ", gateway; 

            else if ($1 == "network" && length(network))
                print "    network ", network; 

            else if ($1 == "dns-nameservers") {
                # Overwrite it if dns is defined.
                # Clear the dns entry if the parameter is empty string
                if (length(dnsVal) && dnsVal != "clear") {
                    print "    dns-nameservers ", dnsVal;
                    # Important - to reset the dns. So that we know whether
                    # dns has been updated to the interfaces file
                    dnsVal = "";
                } else if (remove) {
                    dnsVal = "";    
                } else if (!length(dnsVal)) {
                    print $0;
                }
            }

            else if (!definedRemove) {
                print $0;
            }
        }

        if ($1 == "auto" || $1 == "allow-hotplug" || $1 == "")
        {
            print
        }

        next;
    }

    # If already defined dhcp, then dump the network properties
    if (definedDhcp) {
        writeStatic(address, network, netmask, gateway, dnsVal);
        definedDhcp = 0;
        next;
    } else if (definedManual) {
        writeStatic(address, network, netmask, gateway, dnsVal);
        definedManual = 0;
        next;
    }

    if (!definedRemove) {
        print $0;
    }
}

END {
    if (definedDhcp) {
        # This bit is useful at the condition when the last line is
        # iface dhcp
        writeStatic(address, network, netmask, gateway, dnsVal, device);
    } 
    else if (definedManual) {
        # This bit is useful at the condition when the last line is
        # iface dhcp
        writeStatic(address, network, netmask, gateway, dnsVal, device);
    }
    else if (definedStatic) {
        # Condition for last line and adding dns entry
        if (length(dnsVal) && dnsVal != "clear") {
            if (debug) {
                print "Detected end of line but dns hasn't been updated yet";
            }
            print "    dns-nameservers ", dnsVal;
        }
    }

    if(add)
    {
        print "\nauto", device;
        print "iface",device,"inet manual";
    }
}
