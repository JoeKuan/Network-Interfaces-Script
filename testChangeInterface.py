# Author: Joe Kuan from iTrinegy (www.itrinegy.com). Email: kuan.joe@gmail.com
#
# Due to some contributions have broken this utility.
# I have created this suite of unit tests to make sure none of existing
# operations cannot be compromised
#
# Contributors are permitted to ADD automated tests for their own needs,
# see before __main__ but NOT authorised to CHANGE OR DELETE
# any of the existing tests. Any contribution can be only accepted by passing
# the tests.
import unittest, os, os.path, subprocess

# This is the content for network interface tests
# You are allowed to ADD but NOT allowed to CHANGE or REMOVE any
# of the following interfaces
network_test = """
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet static
address 192.168.202.143
broadcast 192.168.202.255
netmask 255.255.255.0
gateway 192.168.202.254
dns-nameservers 192.168.202.254 192.168.203.254 192.168.200.254 8.8.8.8

auto p3p1
iface p3p1 inet dhcp

auto eth3
iface eth3 inet static
    address 192.168.3.3
    netmask 255.255.255.0
    gateway 192.168.3.1
    dns-search example.com sales.example.com dev.example.com
    dns-nameservers 192.168.3.45 192.168.8.10

auto br0
iface br0 inet static
        address 192.168.0.10
        network 192.168.0.0
        netmask 255.255.255.0
        broadcast 192.168.0.255
        gateway 192.168.0.1
        bridge_ports eth0
        bridge_fd 9
        bridge_hello 2
        bridge_maxage 12
        bridge_stp off

"""

testfile="./network_test"

class NI_TestCase(unittest.TestCase):

    def setUp(self):
        self.assertTrue(os.path.isfile("network_test"), "Expect test sample file")
        self.testOutput = self.__class__.__name__ + ".output"
        self.testSource = testfile
        if os.path.isfile(self.testOutput):
            os.remove(self.testOutput)
        
    def tearDown(self):
        if os.path.isfile(self.testOutput):
            os.remove(self.testOutput)
            
    def numOfDiffLines(self, output=None):
        outfile = self.testOutput
        if output != None:
            outfile = output
        cmd = "diff -w -B -y --suppress-common-lines %s %s" % (outfile, testfile)
        # diff -B doesn't ignore the blank line
        diffCnt = 0
        try:
            lines = subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as e:
            lines = e.output.splitlines()
        for ln in lines:
            if ln.strip() == '>' or ln.strip() == '<':
                continue
            diffCnt += 1
        return diffCnt

    def diffContent(self, output=None):
        outfile = self.testOutput
        if output != None:
            outfile = output
        diff = ''
        try:
            cmd = "diff -w -B -y --suppress-common-lines %s %s 2>&1" % (outfile, testfile)
            subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as e:
            return e.output
        return diff

    # Match the line with header and tail
    def matchLine(self, lines, head, tail):
        found = False
        for ln in lines:
            h, t = ln.split(None, 1)
            if h == head:
                found = True
                self.assertTrue(t.strip() == tail.strip(),
                                "Not matching: %s, %s" % (t.strip(), tail.strip()))
        self.assertTrue(found == True, "No output lines or matching with header %s" % head)

    # Opposite to above method
    def matchNoLine(self, lines, head):
        for ln in lines:
            h, t = ln.split(None, 1)
            self.assertTrue(h != head, "No suppose to contain the linewith %s" % (head))

class StaticChangeAddress(NI_TestCase):

    def runTest(self):
        """ Changing Static Address to Another IP Address """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=eth0 mode=static address=10.0.10.1 gateway=10.0.10.254 netmask=255.255.0.0 > %s" % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit status")
        output = subprocess.check_output("awk -f readInterfaces.awk %s device=eth0" % self.testOutput, shell=True)
        self.assertTrue(output.strip() == "10.0.10.1 255.255.0.0 10.0.10.254",
                        "Actual output " + output.strip() + " but not 10.0.10.1 255.255.0.0 10.0.10.254");
        # Make sure the rest of the content is not corrupted
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 3, "Make sure the rest of the content is not corrupted")

class StaticAddNetworkBroadcast(NI_TestCase):

    def runTest(self):
        """ Add network address on Static entry """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=eth0 mode=static network=192.168.0.0 broadcast=192.168.0.255 > %s" % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit status")
        output = subprocess.check_output("awk -f readInterfaces.awk %s device=eth0 output=all" % self.testOutput,
                                         shell=True)
        lines = output.splitlines()
        self.assertTrue(lines[0].strip() == "192.168.202.143 255.255.255.0 192.168.202.254",
                        "Actual output " + output.strip() + " but not " + "192.168.202.143 255.255.255.0 192.168.202.254");
        self.matchLine(lines, "network", "192.168.0.0")
        # Make sure the rest of the content is not corrupted
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 2, "Make sure the rest of the content is not corrupted" + self.diffContent())

class StaticChangeNetwork(NI_TestCase):

    def runTest(self):
        """ Change network address on Static entry already with network address """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=br0 mode=static network=192.0.0.0 broadcast=192.168.202.0.128 > %s" % (self.testSource, self.testOutput),
                                   shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit status")
        output = subprocess.check_output("awk -f readInterfaces.awk %s device=br0 output=all" % self.testOutput,
                                         shell=True)
        lines = output.splitlines()
        self.assertTrue(lines[0].strip() == "192.168.0.10 255.255.255.0 192.168.0.1",
                        "Basic entry not the same for br0 " + lines[0]);
        self.matchLine(lines, "network", "192.0.0.0")
        # Make sure the rest of the content is not corrupted
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 2, "Make sure the rest of the content is not corrupted" + self.diffContent())

class StaticDeleteNetworkBroadcast(NI_TestCase):
    def runTest(self):
        """ Delete network address on Static entry already with network entry """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=br0 mode=static network= broadcast= > %s" % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit status")
        output = subprocess.check_output("awk -f readInterfaces.awk %s device=br0 output=all" % self.testOutput,
                                         shell=True)
        lines = output.splitlines()
        self.assertTrue(lines[0].strip() == "192.168.0.10 255.255.255.0 192.168.0.1",
                        "Basic entry not the same for br0 " + lines[0]);
        self.matchNoLine(lines, 'network');
        # Make sure the rest of the content is not corrupted
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 2, "Make sure the rest of the content is not corrupted")

class StaticAddDns(NI_TestCase):

    def runTest(self):
        """ Add Dns address on Static entry """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=eth0 mode=static 'dns=192.168.0.1 192.168.0.2 192.168.0.3' > %s"
                                   % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit status")
        output = subprocess.check_output("awk -f readInterfaces.awk %s device=eth0 output=all" % self.testOutput,
                                         shell=True)
        lines = output.splitlines()
        self.matchLine(lines, 'dns-nameservers', '192.168.0.1 192.168.0.2 192.168.0.3')
        # Make sure the rest of the content is not corrupted
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 1, "Make sure the rest of the content is not corrupted")

class StaticChangeDns(NI_TestCase):

    def runTest(self):
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=eth0 mode=static 'dns=192.168.0.1 192.168.0.2 192.168.0.3' > %s"
                                   % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit status")
        # Need sort because the order of output is diff on Linux vs OSX
        output = subprocess.check_output("awk -f readInterfaces.awk %s device=eth0 output=all | sort" % self.testOutput,
                                         shell=True)
        lines = output.splitlines()
        ln = lines[2]
        head, tail = ln.split(None, 1)
        self.assertTrue(head == 'dns-nameservers', "Expect dns-nameservers output: " + head)
        self.assertTrue(tail == "192.168.0.1 192.168.0.2 192.168.0.3",
                        "Actual output " + output.strip() + " but not " +
                        "192.168.0.1 192.168.0.2 192.168.0.3");
        # Make sure the rest of the content is not corrupted
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 1, "Make sure the rest of the content is not corrupted")


class StaticDeleteDns(NI_TestCase):
    def runTest(self):
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=eth0 mode=static 'dns=' > %s"
                                   % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit status")
        output = subprocess.check_output("awk -f readInterfaces.awk %s device=eth0 output=all" % self.testOutput,
                                         shell=True)
        lines = output.splitlines()
        for ln in lines:
            head, tail = ln.split(None, 1)
            self.assertTrue(head != 'dns-nameservers', "Expect no dns-nameservers entry")
        # Make sure the rest of the content is not corrupted
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 1, "Make sure the rest of the content is not corrupted")
                
class DhcpToStaticAddress(NI_TestCase):

    def runTest(self):
        """ Changing DHCP interface to Static IP Address """
        rc = subprocess.check_call("awk -f changeInterface.awk network_test dev=p3p1 mode=static " +
                                   "address=10.0.10.1 gateway=10.0.10.254 netmask=255.255.0.0 > " + self.testOutput,
                                   shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit status")
        output = subprocess.check_output("awk -f readInterfaces.awk %s device=p3p1" % self.testOutput, shell=True)
        self.assertTrue(output.strip() == "10.0.10.1 255.255.0.0 10.0.10.254",
                        "Actual output " + output.strip() + " but not " + "10.0.10.1 255.255.0.0 10.0.10.254");
        # Make sure the rest of the content is not corrupted
        numLines = self.numOfDiffLines()
        # Should be 4 lines diff: interface + address line for each
        self.assertTrue(numLines == 4,
                        "Make sure the rest of the content is not corrupted\n" + self.diffContent())
        
class StaticToDhcpMode(NI_TestCase):
    def runTest(self):
        """ Changing Static Interface to DHCP """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=eth3 mode=dhcp > %s"
                                   % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit status")
        output = subprocess.check_output("awk -f readInterfaces.awk %s device=eth3" % self.testOutput, shell=True)
        self.assertTrue(output.strip() == "dhcp",
                        "Expect dhcp mode");
        # Make sure the rest of the content is not corrupted
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 6,
                        "Make sure the rest of the content is not corrupted\n" + self.diffContent())

class StaticToDhcpModeLastEntry(NI_TestCase):
    def runTest(self):
        """ Changing Static Interface to DHCP Last Entry """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=br0 mode=dhcp > %s"
                                   % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit status")
        output = subprocess.check_output("awk -f readInterfaces.awk %s device=br0" % self.testOutput, shell=True)
        self.assertTrue(output.strip() == "dhcp",
                        "Expect dhcp mode");
        # Make sure the rest of the content is not corrupted
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 11,
                        "Make sure the rest of the content is not corrupted\n" + self.diffContent())

class RemoveDhcp(NI_TestCase):
    def runTest(self):
        """ Remove DHCP Interface """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=p3p1 action=remove > %s"
                                   % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit status")
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_output("awk -f readInterfaces.awk %s device=p3p1" % self.testOutput, shell=True)
            
        # Make sure the rest of the content is not corrupted
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 2,
                        "Make sure the rest of the content is not corrupted\n" + self.diffContent())

class RemoveStatic(NI_TestCase):
    def runTest(self):
        """ Remove Static Interface """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=br0 action=remove > %s"
                                   % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit status")
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_output("awk -f readInterfaces.awk %s device=br0" % self.testOutput, shell=True)
            
        # Make sure the rest of the content is not corrupted
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 12,
                        "Make sure the rest of the content is not corrupted\n" + self.diffContent())

class RemoveNotExist(NI_TestCase):
    def runTest(self):
        """ Remove an a device not exist """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=abc action=remove > %s"
                                   % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit status")
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_output("awk -f readInterfaces.awk %s device=abc" % self.testOutput, shell=True)
            
        # Make sure the rest of the content is not corrupted
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 0,
                        "Make sure the rest of the content is not corrupted\n" + self.diffContent())

        
class RemoveStatic2(NI_TestCase):
    def runTest(self):
        """ Remove first static interface """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=eth0 action=remove > %s"
                                   % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit status")
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_output("awk -f readInterfaces.awk %s device=eth0" % self.testOutput, shell=True)
            
        # Make sure the rest of the content is not corrupted
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 7,
                        "Make sure the rest of the content is not corrupted\n" + self.diffContent())
            
class RemoveMultiple(NI_TestCase):

    def setup(self):
        super(RemoveMultiple, self).setup()
        outfiles = [ self.testOutput + '.1', self.testOutput + '.2',
                     self.testOutput + '.3' ]

        for of in outfiles:
            if os.path.isfile(of):
                os.remove(of)
                
    def runTest(self):
        """ Remove multiple interfaces in sequence """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=eth3 action=remove > %s"
                                   % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit status")
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_output("awk -f readInterfaces.awk %s device=eth3" % self.testOutput, shell=True)
            
        # Make sure the rest of the content is not corrupted
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 7,
                        "Make sure the rest of the content is not corrupted\n" + self.diffContent())

        outfile = self.testOutput + ".1"            
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=p3p1 action=remove > %s"
                                   % (self.testOutput, outfile), shell=True)
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_output("awk -f readInterfaces.awk %s device=p3p1" % outfile, shell=True)
        numLines = self.numOfDiffLines(outfile)
        self.assertTrue(numLines == 9,
                        "Make sure the rest of the content is not corrupted\n" + self.diffContent(outfile))
        
        outfile2 = self.testOutput + ".2"            
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=eth0 action=remove > %s"
                                   % (outfile, outfile2), shell=True)
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_output("awk -f readInterfaces.awk %s device=eth0" % outfile2, shell=True)
        numLines = self.numOfDiffLines(outfile2)
        self.assertTrue(numLines == 16,
                        "Make sure the rest of the content is not corrupted\n" + self.diffContent(outfile2))
        
        outfile3 = self.testOutput + ".3"            
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=br0 action=remove > %s"
                                   % (outfile2, outfile3), shell=True)
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_output("awk -f readInterfaces.awk %s device=br0" % outfile3, shell=True)
        numLines = self.numOfDiffLines(outfile3)
        self.assertTrue(numLines == 28,
                        "Make sure the rest of the content is not corrupted\n" + self.diffContent(outfile3))

    def tearDown(self):
        super(RemoveMultiple, self).tearDown()
        os.remove(self.testOutput + ".1")
        os.remove(self.testOutput + ".2")
        os.remove(self.testOutput + ".3")

class DhcpAdd(NI_TestCase):

    def runTest(self):
        """ Add a basic dhcp entry """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=eth2 action=add mode=dhcp > %s"
                                   % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit")
        out = subprocess.check_output("awk -f readInterfaces.awk %s device=eth2" % self.testOutput, shell=True)
        self.assertTrue(out.strip() == 'dhcp', 'Cannot find added dhcp entry: ' + out)
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 2,
                        "Make sure the rest of the content is not corrupted\n" + self.diffContent())

class DhcpAddExist(NI_TestCase):

    def runTest(self):
        """ Add a dhcp entry already exist """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=p3p1 action=add mode=dhcp > %s"
                                   % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit")
        out = subprocess.check_output("awk -f readInterfaces.awk %s device=p3p1" % self.testOutput, shell=True)
        self.assertTrue(out.strip() == 'dhcp', 'Cannot find added dhcp entry: ' + out)
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 0,
                        "Make sure the rest of the content is not corrupted\n" + self.diffContent())

class DhcpAddStaticExist(NI_TestCase):

    def runTest(self):
        """ Add a dhcp entry which already exist as a static """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=eth0 action=add mode=dhcp > %s"
                                   % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit")
        out = subprocess.check_output("awk -f readInterfaces.awk %s device=eth0" % self.testOutput, shell=True)
        self.assertTrue(out.strip() == 'dhcp', 'Cannot find added dhcp entry: ' + out)
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 6,
                        "Make sure the rest of the content is not corrupted\n" + self.diffContent())

class StaticAdd(NI_TestCase):

    def runTest(self):
        """ Add a basic static entry """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=eth2 action=add mode=static address=10.0.10.12 netmask=255.255.255.0 gateway=10.0.10.254 > %s"
                                   % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit")
        out = subprocess.check_output("awk -f readInterfaces.awk %s device=eth2" % self.testOutput, shell=True)
        self.assertTrue(out.strip() == '10.0.10.12 255.255.255.0 10.0.10.254', 'Cannot find added dhcp entry: ' + out)
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 5,
                        "Make sure the rest of the content is not corrupted\n" + self.diffContent())

class StaticAddFull(NI_TestCase):

    def runTest(self):
        """ Add a basic static full entry """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=eth2 action=add mode=static address=10.0.10.18 netmask=255.255.255.0 gateway=10.0.10.1 network=10.0.0.0 'dns=10.0.10.1 10.0.10.11 10.0.10.77' > %s"
                                   % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit")
        # Need sort because the order of output is diff on Linux vs OSX
        out = subprocess.check_output("awk -f readInterfaces.awk %s device=eth2 output=all | sort" % self.testOutput, shell=True)
        lines = out.splitlines()
        self.assertTrue(len(lines) == 3, "Expect full interface output")
        self.assertTrue(lines[0].strip() == '10.0.10.18 255.255.255.0 10.0.10.1', 'Cannot find added dhcp entry: ' + out)
        head, tail = lines[1].split(None, 1)
        self.assertTrue(head == 'dns-nameservers', "Expect dns output ")
        self.assertTrue(tail == '10.0.10.1 10.0.10.11 10.0.10.77', "Expect dns address")
        head, tail = lines[2].split(None, 1)
        self.assertTrue(head == 'network', "Expect network output ")
        self.assertTrue(tail == '10.0.0.0', "Expect network address")
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 7,
                        "Make sure the rest of the content is not corrupted\n" + self.diffContent())

class StaticAddDhcpExist(NI_TestCase):

    def runTest(self):
        """ Add a basic static entry which DHCP already exist """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=p3p1 action=add mode=static address=10.0.10.12 netmask=255.255.255.0 gateway=10.0.10.254 > %s"
                                   % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit")
        out = subprocess.check_output("awk -f readInterfaces.awk %s device=p3p1" % self.testOutput, shell=True)
        self.assertTrue(out.strip() == '10.0.10.12 255.255.255.0 10.0.10.254', 'Cannot find added dhcp entry: ' + out)
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 4,
                        "Make sure the rest of the content is not corrupted\n" + self.diffContent())

class StaticAddFullDhcpExist(NI_TestCase):

    def runTest(self):
        """ Add a full static entry which DHCP already exist """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=p3p1 action=add mode=static address=196.254.1.2 netmask=255.255.255.96 gateway=196.254.1.128 network=196.254.0.0 dns=196.254.1.128 > %s"
                                   % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit")
        out = subprocess.check_output("awk -f readInterfaces.awk %s device=p3p1 output=all" % self.testOutput, shell=True)
        lines = out.splitlines()
        self.assertTrue(lines[0].strip() == '196.254.1.2 255.255.255.96 196.254.1.128',
                        'Cannot find added dhcp entry: ' + lines[0])
        self.matchLine(lines, 'network', '196.254.0.0')
        self.matchLine(lines, 'dns-nameservers', '196.254.1.128')
        
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 6,
                        "Make sure the rest of the content is not corrupted\n" + self.diffContent())

class StaticAddFullStaticExist(NI_TestCase):

    def runTest(self):
        """ Add a full static entry which static entry already exist """
        rc = subprocess.check_call("awk -f changeInterface.awk %s dev=br0 action=add mode=static address=10.0.10.12 netmask=255.255.128.0 gateway=10.0.10.254 > %s"
                                   % (self.testSource, self.testOutput), shell=True)
        self.assertTrue(rc == 0, "changeInterface.awk non zero exit")
        out = subprocess.check_output("awk -f readInterfaces.awk %s device=br0 output=all" % self.testOutput, shell=True)
        lines = out.splitlines()
        self.assertTrue(lines[0].strip() == '10.0.10.12 255.255.128.0 10.0.10.254',
                        'Cannot find br0 static entry: ' + lines[0])
        self.matchLine(lines, 'network', '192.168.0.0')
        self.matchLine(lines, 'broadcast', '192.168.0.255')
        self.matchLine(lines, 'bridge_fd', '9')
        
        numLines = self.numOfDiffLines()
        self.assertTrue(numLines == 3,
                        "Make sure the rest of the content is not corrupted\n" + self.diffContent())

###########################################
# ADD YOUR OWN TESTS HERE
###########################################

if __name__ == "__main__":

    intf_file = open(testfile, 'w')
    intf_file.write(network_test)
    intf_file.close()
    
    suite = unittest.TestSuite()
    suite.addTest(StaticChangeAddress())
    suite.addTest(DhcpToStaticAddress())
    suite.addTest(StaticToDhcpMode())
    suite.addTest(StaticToDhcpModeLastEntry())
    
    suite.addTest(StaticAddNetworkBroadcast())
    suite.addTest(StaticChangeNetwork())
    suite.addTest(StaticDeleteNetworkBroadcast())
    
    suite.addTest(StaticAddDns())
    suite.addTest(StaticChangeDns())
    suite.addTest(StaticDeleteDns())

    suite.addTest(RemoveDhcp())
    suite.addTest(RemoveStatic())
    suite.addTest(RemoveStatic2())
    suite.addTest(RemoveNotExist())
    suite.addTest(RemoveMultiple())

    suite.addTest(DhcpAdd())
    suite.addTest(DhcpAddExist())
    suite.addTest(DhcpAddStaticExist())

    suite.addTest(StaticAdd())
    suite.addTest(StaticAddFull())
    suite.addTest(StaticAddDhcpExist())
    suite.addTest(StaticAddFullDhcpExist())
    suite.addTest(StaticAddFullStaticExist())
    
    unittest.TextTestRunner(verbosity=2).run(suite)

    os.remove(testfile)
    
