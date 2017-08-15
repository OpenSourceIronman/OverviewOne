# -----------------------------------------------------------------------------
# Code to pack/unpack space packets.
#
# Copyright SpaceVR, 2017.  All rights reserved.
# -----------------------------------------------------------------------------

import struct
import sys
import copy

from pumpkin.core_cmd_tlm import TLM, _bytes_to_dict

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

class Packet(object):
    """ An instance of this object represents a space packet.

    The two primary use cases are:
    1.  Read / deserialize a packet from raw data (for reception)
    2.  Create / serialize a packet to raw data (for transmission)

    Properties:
        DEBUG (static) : enables verbose output when packets are deserialized

        (Primary header)
        pkt_type         : Packet type 
        dst_node         : Destination node
        src_node         : Source node
        service          : Service
        seq_flags        : Sequence flags (0:Cont, 1:First, 2:Last, 3:None)
        seq_count        : Sequence count
        packet_len       : Packet length (excluding primary header, including secondary header)

        (Secondary header)
        scid             : Spacecraft ID
        byp_auth         : Bypass authentication
        checksum_valid   : Checksum valid flag
        ack              : Acknowledge flag
        auth_count       : Auth count
        pkt_subtype      : Packet subtype
        pkt_id           : Packet ID
        pkt_subid        : Packet sub-ID
        checksum         : Checksum value

        (Data)
        data             : bytes or bytearray instance
        data_len         : length of data (excluding primary and secondary headers)
    """

    DEBUG = False

    MAX_DATA_SIZE = 476
    PACKET_SIZE = 512

    SEQ_FLAG_FIRST = 0x01  # This is a bitmask in the 'seq_flags' field.
                           # When set, it indicates the first packet in a sequence.
    SEQ_FLAG_LAST  = 0x02  # This is a bitmask in the 'seq_flags' field.
                           # When set, it indicates the last packet in a sequence.

    def __init__(self, data_with_header=None):
        """ Construct a Packet object

        Args:
            data_with_header : bytes or bytearray instance containing serialized packet
                or None, in which case an empty packet will be constructed
        """

        # Primary header
        self.pkt_type = 0         # Packet type 
        self.dst_node = 0         # Destination node
        self.src_node = 0         # Source node
        self.service = 0          # Service
        self.seq_flags = 0        # Sequence flags (0:Cont, 1:First, 2:Last, 3:None)
        self.seq_count = 0        # Sequence count
        self.packet_len = 0       # Packet length (excluding primary header, including secondary header)

        # Secondary header
        self.scid = 0             # Spacecraft ID
        self.byp_auth = 0         # Bypass authentication
        self.checksum_valid = 0   # Checksum valid flag
        self.ack = 0              # Acknowledge flag
        self.auth_count = 0       # Auth count
        self.pkt_subtype = 0      # Packet subtype
        self.pkt_id = 0           # Packet ID
        self.pkt_subid = 0        # Packet sub-ID
        self.checksum = 0         # Checksum value

        # Data content
        self.data = None

        # Computed values
        # (These are not part of the packet headers or data)
        self.data_len = 0

        # Parse packet data...
        if data_with_header != None:
            self.deserialize(data_with_header)

    def deserialize(self, data_with_header):
        """ Deserialize space packet from a frame of raw data
        
        All class members will be updated.

        Args:
            data_with_header : bytes or bytearray object containing serialized packet
        """

        if isinstance(data_with_header, bytearray):
            data_with_header = str(data_with_header)

        # Unpacks the bytes in 2 byte pairs (3 unsigned shorts) for the primary header
        (ph0, ph1, ph2) = struct.unpack("<3H", data_with_header[0:6])
        # Breaks out each item from the header
        if(ph0 & 0x1000):
            self.pkt_type = 1                           # Packet Type flag
        else:
            self.pkt_type = 0                           # Packet Type flag
        node = (ph0 & 0x07E0) >> 5                      # Node
        if self.pkt_type == 0x00:                       # Assign to src or dst depending on type
          self.src_node = node
          self.dst_node = -1
        else:
          self.dst_node = node
          self.src_node = -1
        self.service = ph0 & 0x001F                     # APID Service
        self.seq_flags = ((ph1 & 0xC000) >> 14)         # Sequence Flags
        self.seq_count = ph1 & 0x3FFF                   # Sequence Count
        self.packet_len = ph2 + 1                       # Packet Length; account for CCSDS convention
        
        # Unpacks the bytes (6 unsigned characters) for the secondary header
        (sh0, sh1, sh2, sh3, sh4, sh5) = struct.unpack("<6B", data_with_header[6:12])
        # Breaks out each item from the header
        self.scid = (sh0 & 0xF0) >> 4                   # Spacecraft ID
        self.byp_auth = (sh0 & 0b00000100) >> 2         # Bypass Authenticate
        if(sh0 & 0x02):                                 # Checksum Valid Flag
            self.checksum_valid = 1
        else:
            self.checksum_valid = 0
        if(sh0 & 0x01):                                 # Acknowledge Flag
            self.ack = 1
        else:
            self.ack = 0
        self.auth_count = sh1                           # Command Auth Count
        self.pkt_subtype = ((sh2 & 0xC0) >> 6)          # Packet Sub-Type
        node = sh3                                      # Node
        if self.pkt_type == 0x00:                       # Assign to src or dst depending on type 
          self.dst_node = node
        else:
          self.src_node = node
        self.pkt_id = sh4                               # Packet ID
        self.pkt_subid = sh5                            # Packet Sub-ID

        # Unpacks the bytes (1 unsigned short) for the checksum
        (self.checksum,) = struct.unpack("<H", data_with_header[-2:])
        
        if Packet.DEBUG: 
            print("\n------------------- primary header -------------------")
            print("Byte Pairs in Hex: %04x  %04x  %04x" % (ph0, ph1, ph2))
            print('Pkt Type: %d (0:TLM, 1:CMD)' % (self.pkt_type))
            if self.pkt_type == 0x00:    print("Source Node: %x"  % (self.src_node))
            else:                   print("Destination Node: %x"  % (self.dst_node))
            print("Service: %x"           %  (self.service))
            print("Seq Flags: %d (0:Cont, 1:First, 2:Last, 3:None)" % (self.seq_flags))
            print("Seq Count: %04x"   %  (self.seq_count))
            print("Number of bytes following primary header: %d" % self.packet_len)
            
            print("------------------- secondary header -------------------")
            print("Bytes in Hex: %02x  %02x  %02x  %02x  %02x  %02x" % (sh0, sh1, sh2, sh3, sh4, sh5))
            print("SCID: %x" % (self.scid))
            print("Checksum Valid: %d" % (self.checksum_valid))
            print("Acknowledge: %d" % (self.ack))
            print("Authenticate Count: %02x" % self.auth_count)
            print("Packet Sub-Type: %d (0:Cmd/Tlm, 1:Data, 2:Control)" % (self.pkt_subtype))
            if self.pkt_type == 0x00:    print("Destination Node: %x"  % (self.dst_node))
            else:                        print("Source Node: %x"  % (self.src_node))
            print("Packet ID: %02x" % self.pkt_id)
            print("Packet Sub-ID: %02x" % self.pkt_subid)
            
            print("------------------- packet checksum -------------------")
            print("Checksum: %04x" % self.checksum)
        
        self.data = data_with_header[12:-2]
        self.data_len = self.packet_len - 6 - 2 # Secondary Header (6) + Checksum (2)

    def serialize(self):
        """ Serialize this space packet and return raw data buffer

        The checksum member will be updated.

        Effects:
            Initializes most primary and secondary header properties.
        """

        if self.data_len > 0 and not isinstance(self.data, bytes) and not isinstance(self.data, bytearray):
            raise ValueError("Data buffer is not bytes.  It is " + repr(type(self.data)))
        if self.data_len > 0 and self.data_len != len(self.data):
            raise ValueError("Data length does not match bytearray size: "+repr(self.data_len)+" vs "+repr(len(self.data)))

        frame = bytearray(Packet.PACKET_SIZE)

        # PRIMARY HEADER
        length = 6 + self.data_len + 2 # Secondary Header (6) + Packet Data + Checksum (2)
        
        ph0  = self.pkt_type << 12 
        if self.pkt_type == 0x00:
          ph0 |= self.src_node << 5
        else:
          ph0 |= self.dst_node << 5

        ph0 |= self.service
        ph1  = self.seq_flags << 14
        ph1 |= self.seq_count
        ph2  = length - 1   # Packet Length; Account for CCSDS convention
        
        if Packet.DEBUG == True:
            print("Primary Header: %04x  %04x  %04x" % (ph0, ph1, ph2))
        struct.pack_into("<3H",frame,0,ph0,ph1,ph2)
        
        # SECONDARY HEADER
        spare = 0x00
        sh0  = self.scid << 4
        sh0 |= self.byp_auth << 2
        sh0 |= self.checksum_valid << 1
        sh0 |= self.ack
        sh1  = self.auth_count
        sh2  = self.pkt_subtype << 6

        if self.pkt_type == 0x00:
          sh2 |= self.dst_node
        else:
          sh2 |= self.src_node

        sh3  = spare
        sh4  = self.pkt_id
        sh5  = self.pkt_subid
        if Packet.DEBUG == True:
            print("Secondary Header: %02x  %02x  %02x  %02x  %02x  %02x" % (sh0, sh1, sh2, sh3, sh4, sh5))
        
        struct.pack_into("<6B",frame,6,sh0,sh1,sh2,sh3,sh4,sh5)
        
        # CHECKSUM
        # find total packet frame length based on data length
        frame_len = 6 + 6 + self.data_len + 2 # Primary Header (6) + Secondary Header (6) + Packet Data + Checksum (2)

        if (self.data != None):
            frame[12:-2] = self.data[0:self.data_len]
                
        self.checksum = 0xFFFF & sum(frame[0:frame_len-2])
        if Packet.DEBUG == True:
            print("csum: 0x%04x" % self.checksum)
        struct.pack_into("<H",frame,frame_len-2,self.checksum)

        # PACKET
        packet = frame[0:frame_len]
        
        return packet


    def make_seq(self):
        """ Split a packet into a sequence of packets, if it is larger than the maximum packet size

        Returns:
            An array of Packet instances, each whose 'data_len' property is less than the
                maximum packet size.
        """

        seq = []

        # Divide by maximum data length (rounding up)
        seq_len = ( (self.data_len-1) // Packet.MAX_DATA_SIZE ) + 1
        # ... and we still need a single packet even if the data is empty
        seq_len = max(1, seq_len)

        next_data = 0

        # Start making copies of the current packet and adding them to the sequence
        for i in range(0, seq_len):
            cur = copy.deepcopy(self)

            # Need to correctly set seq_flags
            cur.seq_flags = 0
            if i == 0:
                cur.seq_flags = cur.seq_flags | Packet.SEQ_FLAG_FIRST
            if i == (seq_len-1):
                cur.seq_flags = cur.seq_flags | Packet.SEQ_FLAG_LAST

            # Copy data, up to maximum packet size
            cur.data_len = self.data_len - next_data
            if cur.data_len > Packet.MAX_DATA_SIZE:
                cur.data_len = Packet.MAX_DATA_SIZE
            if cur.data_len == 0:
                cur.data = None
            else:
                cur.data = self.data[next_data:next_data+cur.data_len]
            next_data = next_data + cur.data_len

            seq.append(cur)

        # Check: final data byte should be at the end of packet buffer
        assert(next_data == self.data_len)
        # Check: we have produced the expected number of packets
        assert(len(seq) == seq_len)

        return seq


class AckPacket(object):
    """ Acknowledgement packet """

    def __init__(self, packet):
        """ Construct an AckPacket from a generic Packet object

        Args:
            packet : base Packet object
        """

        self.base = packet

        # AckPacket specific fields
        self.ack_status = 0     # Status
        self.auth_count = 0     # Authentication count
        self.ext_status = 0     # Exit status

    def deserialize(self):
        if self.base.data_len != 4:
            raise ValueError("Incorrect data length for packet")

        (self.ack_status, self.auth_count, self.ext_status) = struct.unpack("<BBH", self.base.data)
        if Packet.DEBUG:
            print("------------------- packet data -------------------")
            print("Ack Status: %02x (00 is ACK)" % self.ack_status)
            print("Auth Count: %02x" % self.auth_count)
            print("Ext Status: %04x" % self.ext_status)

class TelemetryPacket(object):
    """ Telemetry packet

    Properties:    
        (CDH data)
        self.sys_time
        chd_fault_count 
        system_fault_count
        files_saved
        subsystem_status 
        temp_uc
        system_cmd_count
        cdh_spare

        (ADCS data)
        cmd_status 
        cmd_reject_status 
        cmd_accept_count 
        cmd_reject_count
        tai_seconds
        q_ecef_wrt_eci1 
        q_ecef_wrt_eci2 
        q_ecef_wrt_eci3 
        q_ecef_wrt_eci4
        position_wrt_eci1 
        position_wrt_eci2 
        position_wrt_eci3 
        velocity_wrt_eci1 
        velocity_wrt_eci2 
        velocity_wrt_eci3
        q_body_wrt_eci1 
        q_body_wrt_eci2
        q_body_wrt_eci3 
        q_body_wrt_eci4 
        rotisserie_rate
        adcs_mode
        filtered_speed_rpm1 
        filtered_speed_rpm2 
        filtered_speed_rpm3
        attitude_st1 
        attitude_st2 
        attitude_st3 
        attitude_st4 
        att_status
        rate_est_status 
        sun_point_state 
        sun_vector_body1 
        sun_vector_body2 
        sun_vector_body3 
        sun_vector_status 
        tlm_table_map
        adcs_voltage_5p0 
        adcs_voltage_3p3 
        adcs_voltage_2p5 
        adcs_voltage_1p8 
        adcs_voltage_1p0
        det_temp 
        box1_temp 
        box2_temp 
        motor1_temp 
        motor2_temp 
        motor3_temp 
        bus_voltage
        position_ecef1 
        position_ecef2
        position_ecef3 
        velocity_ecef1 
        velocity_ecef2 
        velocity_ecef3 
        gps_valid
        gps_enabled
        q_tracker_wrt_body1 
        q_tracker_wrt_body2 
        q_tracker_wrt_body3 
        q_tracker_wrt_body4
        adcs_fault_count

        (EPS and Battery data)
        vpcm12v
        vpcm5v
        vpcm3v3
        vpcmbatv
        vidiode_out
        ipcm12v
        ipcm5v
        ipcm3v3
        ipcmbatv
        idiode_out
        vbcr1
        vbcr2
        vbcr3
        vbcr4
        vbcr5
        vbcr6
        vbcr7
        vbcr8
        vbcr9
        battery_voltage_0
        battery_voltage_1
        battery_voltage_2
        temp_battery_0
        temp_battery_1
        temp_battery_2
        temp_motherboard
        temp_daughterboard
        eps_fault_count
        batt_fault_count

        (Radio data)
        radio_state
        rx_commands
        tx_commands
        tx_tlm
        radio_fault_count
        tx_duration
        rx_duration
        xfer_duration
        cycles_remaining
        cycle_time_remaining
        mode_state
        temp_radio

    """

    DEBUG = False

    def __init__(self, packet):
        """ Construct a TelemetryPacket from a generic Packet object

        Args:
            packet : base Packet object
        """

        self.base = packet
        self.values = dict()


    def deserialize(self):
        if self.base.data_len == 266:
            raise ValueError("Telemetry packet is old format.  Check Supernova software version.")
        if self.base.data_len != 247:
            raise ValueError("Incorrect data length for packet: %d" % self.base.data_len)

        packet_name = TLM.name_by_id[self.base.pkt_id]
        bytes_expected = TLM.get_packet_len_bytes(packet_name)
        if self.base.data_len < bytes_expected:
            raise ValueError('{}: expected {} got {} bytes.'.format(packet_name,
                bytes_expected, self.base.data_len))
            
        if TelemetryPacket.DEBUG: print("Telemetry packet : %s" % (packet_name))

        # --- Definitions describe the data items in a packet & their types.
        definitions = TLM.table[packet_name]
        self.values = _bytes_to_dict(self.base.data, definitions)

        if TelemetryPacket.DEBUG: self.printout()
        
    def printout(self):        
        print "\n------------------- packet data -------------------"

        print repr(self.values)

        """
        print 'CDH DATA'
        print '----------'
        print '  sys_time: ' + str(self.sys_time) + ' gps seconds'        
        # print '  chd_fault_count: ' + str(self.chd_fault_count)
        print '  system_fault_count: ' + str(self.system_fault_count)
        print '  system_cmd_count:  ' + str(self.system_cmd_count)
        print '  files_saved: ' + str(self.files_saved)
        print '  subsystem_status: ' + str(self.subsystem_status)
        print 'TEMPERATURE'
        print '  temp_uc: ' + str(self.temp_uc) + ' C'
        
        print 'ADCS DATA'
        print '-------------'
        print 'COMMAND TLM'
        print '  cmd_status: ' + str(self.cmd_status)
        print '  cmd_reject_status: ' + str(self.cmd_reject_status)
        print '  cmd_accept_count: ' + str(self.cmd_accept_count)
        print '  cmd_reject_count: ' + str(self.cmd_reject_count)
        print 'TIME'
        print '  tai_seconds: ' + str(self.tai_seconds*.2)
        print 'ATTITUDE, POSITION, AND VELOCITY'
        print '  q_ecef_wrt_eci1: ' + str(self.q_ecef_wrt_eci1*1e-9)
        print '  q_ecef_wrt_eci2: ' + str(self.q_ecef_wrt_eci2*1e-9)
        print '  q_ecef_wrt_eci3: ' + str(self.q_ecef_wrt_eci3*1e-9)
        print '  q_ecef_wrt_eci4: ' + str(self.q_ecef_wrt_eci4*1e-9)
        print '  position_wrt_eci1: ' + str(self.position_wrt_eci1*2e-5) + ' km'
        print '  position_wrt_eci2: ' + str(self.position_wrt_eci2*2e-5) + ' km'
        print '  position_wrt_eci3: ' + str(self.position_wrt_eci3*2e-5) + ' km'
        print '  velocity_wrt_eci1: ' + str(self.velocity_wrt_eci1*5e-9) + ' km/s'
        print '  velocity_wrt_eci2: ' + str(self.velocity_wrt_eci2*5e-9) + ' km/s'
        print '  velocity_wrt_eci3: ' + str(self.velocity_wrt_eci3*5e-9) + ' km/s'
        print '  q_body_wrt_eci1: ' + str(self.q_body_wrt_eci1*5e-10)
        print '  q_body_wrt_eci2: ' + str(self.q_body_wrt_eci2*5e-10)
        print '  q_body_wrt_eci3: ' + str(self.q_body_wrt_eci3*5e-10)
        print '  q_body_wrt_eci4: ' + str(self.q_body_wrt_eci4*5e-10)
        print '  rotisserie_rate: ' + str(self.rotisserie_rate) + ' rad/s'
        print 'MODE'
        print '  adcs_mode: ' + str(self.adcs_mode) + ' (0:Sun_point, 1:Fine_ref_point)'
        print 'RXN WHEELS: '
        print '  filtered_speed_rpm1: ' + str(self.filtered_speed_rpm1*.4)
        print '  filtered_speed_rpm2: ' + str(self.filtered_speed_rpm2*.4)
        print '  filtered_speed_rpm3: ' + str(self.filtered_speed_rpm3*.4)
        print 'STAR TRACKER'
        print '  attitude_st1: ' + str(self.attitude_st1*4.88e-10)
        print '  attitude_st2: ' + str(self.attitude_st2*4.88e-10)
        print '  attitude_st3: ' + str(self.attitude_st3*4.88e-10)
        print '  attitude_st4: ' + str(self.attitude_st4*4.88e-10)
        print '  att_status: ' + str(self.att_status) + ' (0:OK 2:BAD 3:TOO_FEW_STARS 4:QUEST_FAILED 5:CONVERGING 6:ON_SUN 7:NOT_ACTIVE'
        print '  rate_est_status: ' + str(self.rate_est_status) + ' (0:OK 2:BAD)'
        print 'ATTITUDE CONTROL'
        print '  sun_point_state: ' + str(self.sun_point_state) + ' (2:SEARCH_INIT 3:SEARCHING 4:WAITING 5:CONVERGING 6:ON_SUN 7:NOT_ACTIVE)'
        print 'CSS'
        print '  sun_vector_body1: ' + str(self.sun_vector_body1*0.0001)
        print '  sun_vector_body2: ' + str(self.sun_vector_body2*0.0001)
        print '  sun_vector_body3: ' + str(self.sun_vector_body3*0.0001)
        print '  sun_vector_status: ' + str(self.sun_vector_status) + ' (0:GOOD 1:COARSE 2:BAD)'
        print 'TLM MAP ID'
        print '  tlm_table_map: ' + str(self.tlm_table_map)
        print 'ANALOGS'
        print '  voltage_5p0: ' + str(self.adcs_voltage_5p0*0.025) 
        print '  voltage_3p3: ' + str(self.adcs_voltage_3p3*0.015)
        print '  voltage_2p5: ' + str(self.adcs_voltage_2p5*0.015)
        print '  voltage_1p8: ' + str(self.adcs_voltage_1p8*0.015)
        print '  voltage_1p0: ' + str(self.adcs_voltage_1p0*0.015)
        print '  det_temp: ' + str(self.det_temp*0.8) + ' C'
        print '  box1_temp: ' + str(self.box1_temp*0.005) + ' C'
        print '  box2_temp: ' + str(self.box2_temp*0.005) + ' C'
        print '  motor1_temp: ' + str(self.motor1_temp*0.005) + ' C'
        print '  motor2_temp: ' + str(self.motor2_temp*0.005) + ' C'
        print '  motor3_temp: ' + str(self.motor3_temp*0.005) + ' C'
        print '  bus_voltage: ' + str(self.bus_voltage*0.001)
        print 'GPS'
        print '  position_ecef1: ' + str(self.position_ecef1*2e-5) + ' km'
        print '  position_ecef2: ' + str(self.position_ecef2*2e-5) + ' km'
        print '  position_ecef3: ' + str(self.position_ecef3*2e-5) + ' km'
        print '  velocity_ecef1: ' + str(self.velocity_ecef1*5e-9) + ' km/s'
        print '  velocity_ecef2: ' + str(self.velocity_ecef2*5e-9) + ' km/s'
        print '  velocity_ecef3: ' + str(self.velocity_ecef3*5e-9) + ' km/s'
        print '  gps_valid: ' + str(self.gps_valid) + ' (0:NO 1:YES)'
        print '  gps_enabled: ' + str(self.gps_enabled) + ' (0:NO 1:YES)'
        print 'TRACKER CONTROL'
        print '  q_tracker_wrt_body1: ' + str(self.q_tracker_wrt_body1*1e-9)
        print '  q_tracker_wrt_body2: ' + str(self.q_tracker_wrt_body2*1e-9)
        print '  q_tracker_wrt_body3: ' + str(self.q_tracker_wrt_body3*1e-9)
        print '  q_tracker_wrt_body4: ' + str(self.q_tracker_wrt_body4*1e-9)
        print 'FAULTS'
        print '  adacs_fault_count: ' + str(self.adcs_fault_count)

        print 'POWER DATA'
        print '------------'
        print 'SYSTEM VOLTAGES'
        print '  vpcm12v: ' + str((self.vpcm12v*0.02) - 5.8)
        print '  vpcm5v: ' + str((self.vpcm5v*0.008) - 1.89)
        print '  vpcm3v3: ' + str((self.vpcm3v3*0.0059) - 1.23)
        print '  vpcmbatv: ' + str((self.vpcmbatv*0.0094) - 0.37)
        print '  vidiode_out: ' + str((self.vidiode_out*0.009) - 0.024)
     
        print 'SYSTEM CURRENTS'
        print '  ipcm12v: ' + str((self.ipcm12v*2.063) - 1.95)
        print '  ipcm5v: ' + str((self.ipcm5v*5.289) - 36.448)
        print '  ipcm3v3: ' + str((self.ipcm3v3*5.288) - 14.770)
        print '  ipcmbatv: ' + str((self.ipcmbatv*5.284) - 19.076)
        print '  idiode_out: ' + str((self.idiode_out*14.201) - 7.87)
        print 'BCR VOLTAGES'
        print '  vbcr1: ' + str((self.vbcr1*0.025) - 0.031)
        print '  vbcr2: ' + str((self.vbcr2*0.025) - 0.059)
        print '  vbcr3: ' + str((self.vbcr3*0.01) - 0.002)
        print '  vbcr4: ' + str((self.vbcr4*0.025) - 0.025)
        print '  vbcr5: ' + str((self.vbcr5*0.025) - 0.082)
        print '  vbcr6: ' + str((self.vbcr6*0.025) + 0.006)
        print '  vbcr7: ' + str((self.vbcr7*0.025) - 0.015)
        print '  vbcr8: ' + str((self.vbcr8*0.025) - 0.02)
        print '  vbcr9: ' + str((self.vbcr9*0.025) - 0.03)
        print 'CELL VOLTAGES'
        print '  battery_voltage_0: ' + str((self.battery_voltage_0* -0.011) + 10.165)
        print '  battery_voltage_1: ' + str((self.battery_voltage_1* -0.011) + 10.026)
        print '  battery_voltage_2: ' + str((self.battery_voltage_2* -0.011) + 10.184)
        print 'TEMPERATURE'
        print '  temp_battery_0: ' + str((self.temp_battery_0* -0.314) + 131.392) + ' C'
        print '  temp_battery_1: ' + str((self.temp_battery_1* -0.303) + 130.212) + ' C'
        print '  temp_battery_2: ' + str((self.temp_battery_2* -0.309) + 131.85) + ' C'
        print '  temp_motherboard: ' + str((self.temp_motherboard*0.372) - 273.15) + ' C'
        print '  temp_daughterboard: ' + str((self.temp_daughterboard*0.372) - 273.15) + ' C'
        print 'FAULTS'
        print '  eps_fault_count: ' + str(self.eps_fault_count)
        print '  batt_fault_count: ' + str(self.batt_fault_count)
    
        print 'RADIO DATA'
        print '------------'
        print 'CONTROL BLOCK'
        print '  radio_state: ' + str(self.radio_state)
        print '  rx_commands: ' + str(self.rx_commands)
        print '  tx_commands: ' + str(self.tx_commands)
        print '  tx_tlm: ' + str(self.tx_tlm)
        print 'FAULTS'
        print '  radio_fault_count: ' + str(self.radio_fault_count)
        print 'TLM BURST STATS'
        print '  tx_duration: ' + str(self.tx_duration)
        print '  rx_duration: ' + str(self.rx_duration)
        print '  cycles_remaining: ' + str(self.cycles_remaining)
        print '  cycle_time_remaining: ' + str(self.cycle_time_remaining)
        print '  mode_state: ' + str(self.mode_state)
        print 'TEMPERATURE'
        print '  temp_radio: ' + str(self.temp_radio) + ' C'
        """

