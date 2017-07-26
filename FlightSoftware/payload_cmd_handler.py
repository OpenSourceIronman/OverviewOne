#!/usr/bin/env python2.7

import sys
import subprocess
import shlex

from agent import Agent
from supernova import Supernova
from spacepacket import Packet
from send import Send

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

class PayloadCommandHandler:
    """ Dispatches a packet to a handler method based on its packet ID.

        This class also provides a set of handler implementations.
            * 'run_shell_cmd' - executes a command string in the system shell
                   and returns the result
    """

    DEBUG = False

    # These are arbitrary command codes for the common payload-specific
    # commands that this class implements by default.
    SHELL_CMD  = 0x00
    SHELL_RESP = 0x80
    ECHO_CMD   = 0x01
    ECHO_RESP  = 0x81

    def __init__(self):
        # Map of command IDs to handler methods.
        self.handlers = {
            PayloadCommandHandler.SHELL_CMD  : PayloadCommandHandler.run_shell,
            PayloadCommandHandler.ECHO_CMD   : PayloadCommandHandler.run_echo,

            PayloadCommandHandler.SHELL_RESP : Agent.do_nothing,
            PayloadCommandHandler.ECHO_RESP  : Agent.do_nothing
        }

    def dispatch(self, packet):
        """ Given a packet that is a payload command, dispatch to handler based on its ID.

        This function can has a signature that can be used as the main Agent
        handler for all incoming payload command requests.  For example:

            Agent().handler["Payload Command"] = PayloadCommandHandler().dispatch
        """

        if type(packet) is not Packet:
            raise TypeError("Expected packet")

        cmd = packet.pkt_id
        if cmd in self.handlers:
            if PayloadCommandHandler.DEBUG:
                print("Known command %x" % (cmd))
            self.handlers[cmd](packet)
        else:
            if PayloadCommandHandler.DEBUG:
                print("Unknown command %x.  Ignoring." % (cmd))


    shell_cmd = ""
    shell_rsl = ""
    @staticmethod
    def run_shell(packet):
        """ The "shell" command runs a bash command.

        It can be split across multiple packets, in which case
        the string will be accumulated between the first and
        last packets, and it will be run when the last packet
        is received.
        """

        if (packet.seq_flags & Packet.SEQ_FLAG_FIRST):
            # On the first packet, clear whatever old command string
            PayloadCommandHandler.shell_cmd = ""

        PayloadCommandHandler.shell_cmd = PayloadCommandHandler.shell_cmd + packet.data.decode("utf-8")
        shell_cmd = PayloadCommandHandler.shell_cmd

        if (packet.seq_flags & Packet.SEQ_FLAG_LAST):

            # On the last packet, we actually run the command
            print("Running in shell...\n $ %s \n" % (shell_cmd))

            # TODO: add some safeguards against timeout, exceptions, etc.
            shell_rsl = subprocess.check_output(shell_cmd, shell=True)
            # shell_rsl = subprocess.check_output(shlex.split(shell_cmd), shell=False) # if we don't want to use shell

            if PayloadCommandHandler.DEBUG:
                print('================= BEGIN OUTPUT =================')
                print(shell_rsl)
                print('================== END OUTPUT ==================')

            # Send reponse packet
            #TODO: are the src/dest wrong?
            #send_payload_cmd(packet.dst_node, packet.src_node, PayloadCommandHandler.SHELL_RESP, shell_rsl)
            Send.send_payload_cmd(4, 4, PayloadCommandHandler.SHELL_RESP, shell_rsl)

    @staticmethod
    def run_echo(packet):
        """ The "echo" command simply sends back a packet with the same data.

        """

        #TODO: are the src/dest wrong?
        #send_payload_cmd(packet.dst_node, packet.src_node, PayloadCommandHandler.ECHO_RESP, shell_rsl)
        Send.send_payload_cmd(4, 4, PayloadCommandHandler.ECHO_RESP, packet.data)
