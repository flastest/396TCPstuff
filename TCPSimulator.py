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
import random
from packet import TCPPacket
from pqueue import PriorityQueue

# Constants

MAX_PACKET_DATA = 4
TRANSMISSION_DELAY = 5
LOST_PACKET_PROBABILITY = 0.25
ROUND_TRIP_TIME = 2 * TRANSMISSION_DELAY
TIMEOUT = 2 * ROUND_TRIP_TIME
DEBUG = False



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
        #print("Here lies the current event queue:",eventQueue)
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
    def __str__(self):
        return "Client"


    #returns the number of the packet it's lookingfor
    def getSeq(self):
        return self.seq
    


    def receivePacket(self, p, eventQueue, t):
        """Handles receipt of the acknowledgment packet."""
        self.seq = p.ack
        self.ack = p.seq + len(p.data) # irrelevant, idk why this is here
        
        # this is where the stuff needs to go, the thing that tells
        # it to keep track of all the acks it has and stuff.
        # it needs to chill, the acks come in at whatever speed, but 
        #maybe this should send the nextXPackets

        #cool I got an ack, now I need to choose how to respond
        if DEBUG:
            print("receiving packet! now I should send %r" % self.ack )
            print(str(eventQueue))
        if self.seq < len(self.msgBytes) + len(p.data):
            
            self.sendXPackets(eventQueue,t,self.x)
            #self.sendNextPacket(eventQueue, t)
    


    def queueRequestMessage(self, eventQueue, t):
        """Enqueues a RequestMessageEvent at time t."""
        e = RequestMessageEvent(self)
        eventQueue.enqueue(e, t)



    def requestMessage(self, eventQueue, t):
        """Initiates transmission of a message requested from the user."""
        msg = input("Enter a message: ")
        if (len(msg) != 0):
            print("Client sends \"" + msg + "\"")
            self.msgBytes = msg.encode("UTF-8")
            self.seq = 0
            self.ack = 0
            self.sendNextPacket(eventQueue, t)



    def requestXPackets(self, eventQueue, t):
        msg = input("Enter a message: ")

        #add the right amount of spaces to the end of the word to make it fit
        # without this, the last ack is not a multiple of 4.
        if False:
            numSpaces = len(msg) % 4
            msg += numSpaces * " "


        windowSize = int(input("how big should the receive window be?"))
        if (len(msg) != 0):
            print("Client sends \"" + msg + "\"")
            self.msgBytes = msg.encode("UTF-8")
            self.seq = 0
            self.ack = 0
            self.x = windowSize
            self.sendXPackets(eventQueue, t,windowSize)

    def sendXPackets(self,eventQueue,t,x):
        
        #creates the packets
        packets = []
        for i in range(x):
            nBytes = min(MAX_PACKET_DATA, len(self.msgBytes) - self.seq)
            


            data = self.msgBytes[self.seq:self.seq + nBytes]

            p = TCPPacket(seq=self.seq,ack=self.ack,ACK =True, data=data) # no reason to have ack here?
            #adding the checksum to the packet
            p.checksum = (checksum16(p.toBytes()) ^ 0xFFFF ) 
            packets.append(p)

            # if self.seq extends the amount of data in msgBytes, there're 
            # no more packets to make
            if self.seq +  (len(p.data))>= len(self.msgBytes):
                #this will be the last packet
                if DEBUG:
                    print('all the packets are sent!')
                
                p.FIN = True
                #at this point, also need to recalculate the checksum
                p.checksum = 0x0000
                p.checksum = (checksum16(p.toBytes()) ^ 0xFFFF ) 
            
                break

            #add to sequence
            self.seq += nBytes



        #now to send all the packets!
        for p in packets:
            e = ReceivePacketEvent(self.server, p)

            #there's a chance that the packet WON'T be lost:        
            if(random.random()>LOST_PACKET_PROBABILITY):
                if DEBUG:
                    print("packet %r isn't lost"% p.data)
                eventQueue.enqueue(e, t + TRANSMISSION_DELAY)
                #I'm moving this to when the serverreceives the last message
                #if p.FIN:
                    #self.queueRequestMessage(eventQueue, 66 +t + ROUND_TRIP_TIME)
            else: 
                #if lost
                #if DEBUG:
                print("packet %r is LOST!!!"% p.data)


            #remember to add a timeout event
            toe = TimeoutEvent(self.server, p)
            eventQueue.enqueue(toe, t + 2*TRANSMISSION_DELAY)
            t+=1
        if DEBUG:
            print("all packets in this batch are sent")
            print("here's the event queue:",str(eventQueue))




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
        if(random.random()>LOST_PACKET_PROBABILITY):

            eventQueue.enqueue(e, t + TRANSMISSION_DELAY)
            if p.FIN:
                # if this is the last packet, it will start over. 
                self.queueRequestMessage(eventQueue, t + ROUND_TRIP_TIME)
        
        #remember to add a timeout event
        #toe = TimeoutEvent(self.server, p)
        toe = TimeoutEvent(self, p)
        eventQueue.enqueue(toe, t + 2*TRANSMISSION_DELAY)




    

    

class TCPServer:
    """
    This class implements the server side of the simulation, which
    receives packets from the client side.
    """

    def __init__(self):
        self.resetForNextMessage()
        self.seq = 0
        self.ack = 0
        # this is a list of the packets' acks
        self.receivedPackets = []

    def __str__(self):
        return "Server"

    #returns the number of the packet it's lookingfor
    def getSeq(self):
        return self.seq

    def resetForNextMessage(self):
        """Initializes the data structures for holding the message."""
        self.msgBytes = bytearray()
        self.ack = 0
        self.seq = 0
        self.receivedPackets =[]


    def receivePacket(self, p, eventQueue, t):
        """
        Handles packets sent from the server and sends an acknowledgment
        back in return.  This version assumes that the sequence numbers
        appear in the correct order.
        """

        ##
        ## THIS JUST SENDS THE ACK!!
        ## 



        #self.msgBytes.extend(p.data)
        if p.seq == self.seq:
            self.seq+= len(p.data)
            self.msgBytes.extend(p.data)
        

        #there used to be something here that kept track of received packets
        # so that client didn't need to resend EVERYTHING, but I didn't implement
        # it well so I deleted it.

        self.ack = self.seq

        if DEBUG:
            print("server received %r and its seq/ack is now %r" % (p.data,self.ack))
        reply = TCPPacket(seq=self.seq, ack=self.ack, ACK=True)
        


        if p.FIN and self.ack >= p.seq: #I should also check here to make sure last complete set is here
            reply.FIN = True
            
            print("Server receives \"" + self.msgBytes.decode("UTF-8") + "\"")
            if DEBUG:
                print("Cool I got all the packets! ")
            self.resetForNextMessage()
            eventQueue.clear()
            self.client.queueRequestMessage(eventQueue, t + ROUND_TRIP_TIME)

        #adding the checksum to the packet
        reply.checksum = (checksum16(reply.toBytes()) ^ 0xFFFF ) 


        # here is where we should send the ack
        e = ReceivePacketEvent(self.client, reply)
        eventQueue.enqueue(e, t + TRANSMISSION_DELAY)

    

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
        #self.client.requestMessage(eventQueue, t)
        self.client.requestXPackets(eventQueue,t)


class TimeoutEvent(TCPEvent):
    '''
    This is called when a packet is lost!
    '''
    def __init__(self,handler,packet):#,otherGuy):
        TCPEvent.__init__(self)
        self.handler = handler
        self.packet = packet
        #self.other = otherGuy #this is the other computer, not this one
    def __str__(self):
        return "TimeoutPacket("+str(self.packet)+")"


    # have to resend packet if packet hasn't been received by the time this
    # event comes up.
    def dispatch(self,eventQueue,t):
        if DEBUG:
            print("TIMEOUT EVENT~!")
            print("right now the",str(self.handler),"'s sequence is ",self.handler.getSeq())

            print("I'm the timout event for %r with a seq of %r" % (self.packet.data,self.packet.seq))
        # nothing happens if we don't need this packet resent 
        if self.handler.getSeq() - len(self.packet.data)>= self.packet.seq:
            if DEBUG:
                print("packet",self.packet,"doesn't need to be resent")
            
        else:
                # if we're still waiting for the packet, resend it.
            
            print("resending packet",self.packet.seq,":",self.packet.data,"and everything after it")
            
            #there's a chance that the packet will be lost:
            if(random.random()>LOST_PACKET_PROBABILITY):
                
                e = ReceivePacketEvent(self.handler, self.packet)
                eventQueue.enqueue(e, t + TRANSMISSION_DELAY)
            
            # timeout for the resent message 
            toe = TimeoutEvent(self.handler, self.packet)
            eventQueue.enqueue(toe, t + 2*TRANSMISSION_DELAY)

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
        p =self.packet
        # check the checksum
        curentCheckSum = p.checksum
        p.checksum = 0x0000
        calculatedChecksum = checksum16(p.toBytes())
        p.checksum = curentCheckSum
        # print("cur check is ",(curentCheckSum))
        # print("trying it gives" , (calculatedChecksum))
        # print("if you add those you get ",(curentCheckSum + calculatedChecksum))
        # print("the hex of that is ", hex(curentCheckSum + calculatedChecksum))
        if (curentCheckSum + calculatedChecksum) != 0xFFFF:
            print("checksum addition for",self.packet.data,"failed, got ",hex(curentCheckSum + checksum16(p.toBytes())) )
            #should probably drop the packet if checksum fails...



        # self.handler.receivePacket triggers the next packets to send
        self.handler.receivePacket(self.packet, eventQueue, t)

# Startup code

if __name__ == "__main__":
    TCPSimulator()
