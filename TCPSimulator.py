# File: TCPSimulator.py

"""
This module implements the starter version of the TCP simulator assignment.
"""

# Implementation notes for Problem Set 5
# --------------------------------------
# For Problem 1, you will need to add more state information to both the
# TCPClient and TCPServer classes to keep track of which bytes have been
# acknowledged.  You will also need to implement a new TCPEvent subclass
# called TimeoutEvent that implements the response to a packet timeout.
# Sending a packet should also post a TimeoutEvent for a later time.
# If the packet has been acknowledged, the TimeoutEvent handler can simply
# ignore it.  If not, the TimeoutEvent handler should resend the packet.
#
# Problem 2 requires relatively little code beyond Problem 1, assuming
# that you have coded Problem 1 correctly (bugs in Problem 1 are likely
# to manifest themselves here when there are multiple pipelined messages).
# The priority queue strategy means that you don't need to use any
# Python primitives for parallelism such as timeouts and threads.
#
# Problem 3 means that you need to have the client keep track of the
# number of unacknowledged packets and to pay attention to the receive
# window in the acknowledgments that come in from the server.

from packet import TCPPacket
from pqueue import PriorityQueue

# Constants

MAX_PACKET_DATA = 4
TRANSMISSION_DELAY = 5
LOST_PACKET_PROBABILITY = 0.25
ROUND_TRIP_TIME = 2 * TRANSMISSION_DELAY
TIMEOUT = 2 * ROUND_TRIP_TIME

EVENT_TRACE = False              # Set this flag to enable event tracing

def TCPSimulator():
    """
    This function implements the test program for the assignment.
    It begins by creating the client and server objects and then
    executes an event loop driven by a priority queue for which
    the priority value is time.
    """
    eventQueue = PriorityQueue()
    client = TCPClient()
    server = TCPServer()
    client.server = server
    server.client = client
    client.queueRequestMessage(eventQueue, 0)
    while not eventQueue.isEmpty():
        e,t = eventQueue.dequeueWithPriority()
        if EVENT_TRACE:
            print(str(e) + " at time " + str(t))
        e.dispatch(eventQueue, t)


# my checksum16 function. I don't know how the hell to deal with bytearrays, so 
# i spent sometime writing around that. From what I can tell, byte arrays
# are hard to use garbage. The internet wasn't particulary helpful. I wrote
# a ton of helper functions to convert the bytes into bits because binary operations
# on the bytes gave me really weird bugs.

# while I did convert the bytes into ints, I treated them like bits and did all
# the bitwise operations on them and stuff. I know my way around bitwise operations
# and << and >> but bytearray really wasn't doing anything for me so I found a nicer
# way of converting bytes into words. It was just easier to make a long list of bits.
# I'm sorry if this isn't what you're looking for, but bytearray was hard to use.

def checksum16(data):
    #convert data into a useful format
    listOfBits = []
    for i in data:
        newBinary = getBinary(i)
        for j in newBinary:
            listOfBits.append(int(j))   
    halfwords = getHalfWords(listOfBits)

    checksumBits = calculatechecksum(halfwords)
    REALCHECKSUM = convertToBytes(checksumBits)
    return REALCHECKSUM

#this converts a string of bits into bytes
def convertToBytes(bits):
    bytesArray = bytearray()
    total = 0
    for i in range(len(bits)):
        total += (2**(15-i)* bits[i])
    return total



# given a list of halfwords, calculates a checksum
def calculatechecksum(halfwords):
    total = [0]*16
    overflow = 0
    for currentHalfWord in halfwords:
        # want to keep checking until overflow is no more
        while (True):
            for i in range(15,-1,-1):
                #check every bit in the halfword
                
                overflowWillBe = (total[i] & currentHalfWord[i]) | (overflow & currentHalfWord[i]) | (total[i] & overflow)
                total[i] = (total[i] ^ currentHalfWord[i] ^ overflow) | (overflow & total[i] & currentHalfWord[i])
                overflow = overflowWillBe
               
            #checking to make sure that we don't have to loop over again
            if overflow == 0:
                break;
    return total


#from a list of bits, divide them into segments of 16
def getHalfWords(listOfBits):
    halfWordList = []
    while(len(listOfBits)>0):
        # if the number of bytes is odD:
        if len(listOfBits) < 16:
            # so if there's no room for another whole half word, we just
            # have to add zeros to the end 
            numSpacesLeft = 16 - len(listOfBits)
            newZeros = [0] * numSpacesLeft
            listOfBits+=(newZeros)

        halfWordList.append(listOfBits[:16])
        listOfBits = listOfBits[16:]
    return halfWordList

def getBinary(byte):
  ans =  bin(byte)
  ans = ans[2:] # getting rid of all the garbage at the beginning
  # now have to add the right amount of 0s to the beginning
  numZerosToAdd = 8 - len(ans)
  return "0"*numZerosToAdd + ans

# gets a byte from a string of binary numbers
def getByte(bits):
  return bytearray(int(bits,2))











class TCPClient:
    """
    This class implements the client side of the simulation, which breaks
    up messages into small packets and then sends them to the server.
    """
    
    def __init__(self):
        """Initializes the client structure."""


    #returns the number of the packet it's lookingfor
    def getSeq(self):
        return self.seq


    def requestMessage(self, eventQueue, t):
        """Initiates transmission of a message requested from the user."""
        msg = input("Enter a message: ")
        if (len(msg) != 0):
            print("Client sends \"" + msg + "\"")
            self.msgBytes = msg.encode("UTF-8")
            self.seq = 0
            self.ack = 0
            self.sendNextPacket(eventQueue, t)

    def sendNextPacket(self, eventQueue, t):
        """Sends the next packet in the message."""
        nBytes = min(MAX_PACKET_DATA, len(self.msgBytes) - self.seq)
        data = self.msgBytes[self.seq:self.seq + nBytes]
        p = TCPPacket(seq=self.seq, ack=self.ack, ACK=True, data=data)
        if self.seq + nBytes == len(self.msgBytes):
            p.FIN = True

        #adding the checksum to the packet
        p.checksum = (checksum16(p.toBytes()) ^ 0xFFFF ) 


        #adds event for server to receive this packet
        e = ReceivePacketEvent(self.server, p)



        #there's a chance that the packet will be lost:
        import random
        if(random.random()>LOST_PACKET_PROBABILITY):

            eventQueue.enqueue(e, t + TRANSMISSION_DELAY)
            if p.FIN:
                self.queueRequestMessage(eventQueue, t + ROUND_TRIP_TIME)
        
        #remember to add a timeout event
        toe = TimeoutEvent(self.server, p)
        eventQueue.enqueue(toe, t + 2*TRANSMISSION_DELAY)


    def receivePacket(self, p, eventQueue, t):
        """Handles receipt of the acknowledgment packet."""
        self.seq = p.ack
        self.ack = p.seq + 1
        if self.seq < len(self.msgBytes):
            self.sendNextPacket(eventQueue, t)

    def queueRequestMessage(self, eventQueue, t):
        """Enqueues a RequestMessageEvent at time t."""
        e = RequestMessageEvent(self)
        eventQueue.enqueue(e, t)

class TCPServer:
    """
    This class implements the server side of the simulation, which
    receives packets from the client side.
    """

    def __init__(self):
        self.resetForNextMessage()

    #returns the number of the packet it's lookingfor
    def getSeq(self):
        return self.seq

    def receivePacket(self, p, eventQueue, t):
        """
        Handles packets sent from the server and sends an acknowledgment
        back in return.  This version assumes that the sequence numbers
        appear in the correct order.
        """
        # check the checksum

        curentCheckSum = p.checksum
        p.checksum = 0x0000
        calculatedChecksum = checksum16(p.toBytes())
        p.checksum = curentCheckSum
        #print("cur check is ",hex(curentCheckSum))
        #print("trying it gives" , hex(checksum16(p.toBytes())))
        if (curentCheckSum + calculatedChecksum) != 0xFFFF:
            print("checksum addition failed, got ",hex(curentCheckSum + checksum16(p.toBytes())))
 

        self.msgBytes.extend(p.data)
        self.seq = p.ack
        self.ack = p.seq + len(p.data)
        reply = TCPPacket(seq=self.seq, ack=self.ack, ACK=True)
        if p.FIN:
            reply.FIN = True
            print("Server receives \"" + self.msgBytes.decode("UTF-8") + "\"")
            self.resetForNextMessage()


        e = ReceivePacketEvent(self.client, reply)
        eventQueue.enqueue(e, t + TRANSMISSION_DELAY)
        #remember to add a timeout event
        toe = TimeoutEvent(self.client, reply)
        eventQueue.enqueue(toe, t + 2*TRANSMISSION_DELAY)

    def resetForNextMessage(self):
        """Initializes the data structures for holding the message."""
        self.msgBytes = bytearray()
        self.ack = 0


class TCPEvent:
    """
    This abstract class is the base class of all events that can be
    entered into the event queue in the simulation.  Every TCPEvent subclass
    must define a dispatch method that implements that event.
    """

    def __init__(self):
        """Each subclass should call this __init__ method."""

    def dispatch(self, eventQueue, t):
        raise Error("dispatch must be implemented in the subclasses")


class RequestMessageEvent(TCPEvent):
    """
    This TCPEvent subclass triggers a message transfer by asking
    the user for a line of text and then sending that text as a
    TCP message to the server.
    """

    def __init__(self, client):
        """Creates a RequestMessageEvent for the client process."""
        TCPEvent.__init__(self)
        self.client = client

    def __str__(self):
        return "RequestMessage(client)"

    def dispatch(self, eventQueue, t):
        self.client.requestMessage(eventQueue, t)

class TimeoutEvent(TCPEvent):
    '''
    This is called when a packet is lost!
    '''
    def __init__(self,handler,packet):
        TCPEvent.__init__(self)
        self.handler = handler
        self.packet = packet
    def __str__(self):
        return "TimeoutPacket("+str(self.packet)+")"
    
    # have to resend packet if packet hasn't been received by the time this
    # event comes up.
    def dispatch(self,eventQueue,t):
        # nothing happens if we don't need this packet resent 
        if self.handler.getSeq() >= self.packet.seq:
            return
        # if we're still waiting for the packet, resend it.
        print("resending packet:",self.packet.seq,":",self.packet.data)
        e = ReceivePacketEvent(self.handler, self.packet)
        eventQueue.enqueue(e, t + TRANSMISSION_DELAY)


class ReceivePacketEvent(TCPEvent):
    """
    This TCPEvent subclass is called on each packet.
    """

    def __init__(self, handler, packet):
        """
        Creates a new ReceivePacket event.  The handler parameter is
        either the client or the server.  The packet parameter is the
        TCPPacket object.
        """
        TCPEvent.__init__(self)
        self.handler = handler
        self.packet = packet

    def __str__(self):
        return "ReceivePacket(" + str(self.packet) + ")"

    def dispatch(self, eventQueue, t):
        self.handler.receivePacket(self.packet, eventQueue, t)

# Startup code

if __name__ == "__main__":
    TCPSimulator()
