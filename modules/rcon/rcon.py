﻿import socket
import os
import sys
import re
import zlib
import binascii

#Author: Yoshi_E
#Date: 2019.06.14
#https://www.battleye.com/downloads/BERConProtocol.txt
#Code based on https://github.com/felixms/arma-rcon-class-php

class ARC():

    def __init__(self, serverIP, RConPassword, serverPort = 2302, options = {}):

        self.options = {
            'timeoutSec'    : 1,
            'autosaveBans'  : False,
            'debug'         : False
        }
        
        self.socket = None;
        #bool Status of the connection
        self.disconnected = True
        #string Head of the message, which was sent to the server
        self.head = None;
        #int Sequence number and also a helper to end loops.
        self.end = 0 # required to remember the sequence.
        
        if (type(serverPort) != int or type(RConPassword) != str or type(serverIP) != str):
            raise Exception('Wrong constructor parameter type(s)!')
        self.serverIP = serverIP
        self.serverPort = serverPort
        self.rconPassword = RConPassword
        self.options = {**self.options, **options}
        self.checkOptionTypes()
        self.checkForDeprecatedOptions()
        self.connect()

    
    #Class destructor
    def __del__(self):
        self.disconnect()
    
    #Closes the connection
    def disconnect(self):
        if (self.disconnected):
            return None
        self.socket.close() #fclose(self.socket)
        self.socket = None
        self.disconnected = True
    
    #Creates a connection to the server
    def connect(self):
        if (self.disconnected == False):
            self.disconnect()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #
        self.socket.connect((self.serverIP,  self.serverPort)) # #"udp://"+
        self.socket.settimeout(self.options['timeoutSec']) #stream_set_timeout(self.socket, self.options['timeoutSec'])
        if (self.socket == False):
            raise Exception('Failed to create socket!')
        
        self.socket.setblocking(1)
        self.authorize()
        self.disconnected = False

    
    #Closes the current connection and creates a new one
    def reconnect(self):
        if (self.disconnected == False):
            self.disconnect()
        self.connect()
        return None
    

    #Checks if ARC's option array contains any deprecated options
    def checkForDeprecatedOptions(self):
        if ('timeout_sec' in self.options):
            raise Exception("The 'timeout_sec' option is deprecated since version 2.1.2 and will be removed in 3.0. Use 'timeoutSec' instead.")
            self.options['timeoutSec'] = self.options['timeout_sec']
    
        if ('heartbeat' in self.options or 'sendHeartbeat' in self.options):
            raise Exception("Sending a heartbeat packet is deprecated since version 2.2.")
    

    
    #Validate all option types
    def checkOptionTypes(self):
        if (type(self.options['timeoutSec']) != int):
            raise Exception("Expected option 'timeoutSec' to be integer, got %s" % type(self.options['timeoutSec']))
        if (type(self.options['autosaveBans']) != bool):
            raise Exception("Expected option 'autosaveBans' to be boolean, got %s" % type(self.options['autosaveBans']))
        if (type(self.options['debug']) != bool):
            raise Exception("Expected option 'debug' to be boolean, got %s" % type(self.options['debug']))

    
    #Sends the login data to the server in order to send commands later
    def authorize(self):
        sent = self.writeToSocket(self.getLoginMessage())
        if (sent == False):
            raise Exception('Failed to send login!')
        result = self.socket.recv(16).decode("iso-8859-1") #fread(self.socket, 16)
        if (ord(result[len(result)-1]) == 0): #ignore error
            raise Exception('Login failed, wrong password or wrong port!')
    

    
    #Receives the answer form the server
    def getResponse(self):
        output = ''   
        answer = ""
        while(True):
            try:
                self.socket.settimeout(1)
                answer = self.socket.recv(102400)[len(self.head):].decode("iso-8859-1") # #substr(fread(self.socket, 102400), len(self.head))
            except:
                answer = "" #timed out
            while ('RCon admin' in answer): #Flushing Stream
                try:
                    self.socket.settimeout(1)
                    answer = self.socket.recv(102400)[len(self.head):].decode("iso-8859-1") # #substr(fread(self.socket, 102400), len(self.head))
                except:
                    answer = "" #timed out
            output += answer  
            if(answer == ""):
                break
            self.socket.settimeout(self.options['timeoutSec'])
        return output

    #The heart of None class - None function actually sends the RCon command
    def send(self, command):
        if (self.disconnected):
            raise Exception('Failed to send command, because the connection is closed!')
    
        msgCRC = self.getMsgCRC(command)
        head = 'BE'+chr(int(msgCRC[0],16))+chr(int(msgCRC[1],16))+chr(int(msgCRC[2],16))+chr(int(msgCRC[3],16))+chr(int('ff',16))+chr(int('01',16))+chr(int('0',16))
        msg = head+command
        self.head = head
        if (self.writeToSocket(msg) == False):
            raise Exception('Failed to send command!')
    
    #Writes the given message to the socket
    def writeToSocket(self, message):
        return self.socket.send(bytes(message.encode("iso-8859-1"))) #fwrite(self.socket, message)
    
    #Debug funcion to view special chars
    def String2Hex(self,string):
        phex=''
        for i in range(0, len(string)):
            phex += format(ord(string[i]), 'x')
        return phex

    #Generates the password's CRC32 data
    def getAuthCRC(self):
        str = self.String2Hex(chr(255)+chr(0)+self.rconPassword.strip())
        str = (chr(255)+chr(0)+self.rconPassword.strip()).encode("iso-8859-1")
        authCRC = '%x' % zlib.crc32(bytes(str))
        authCRC = [authCRC[-2:], authCRC[-4:-2], authCRC[-6:-4], authCRC[0:2]] #working
        return authCRC
    
    #Generates the message's CRC32 data
    def getMsgCRC(self, command):
        str = bytes(((chr(255)+chr(1)+chr(int('0',16))+command).encode("iso-8859-1")))
        msgCRC = '%x' % zlib.crc32(str)
        msgCRC = [msgCRC[-2:], msgCRC[-4:-2], msgCRC[-6:-4], msgCRC[0:2]]
        return msgCRC
    
    #Generates the login message
    def getLoginMessage(self):
        authCRC = self.getAuthCRC()
        loginMsg = 'BE'+chr(int(authCRC[0],16))+chr(int(authCRC[1],16))+chr(int(authCRC[2],16))+chr(int(authCRC[3],16))
        loginMsg += chr(int('ff',16))+chr(int('00',16))+self.rconPassword
        return loginMsg
    
    #Returns the socket used by ARC, might be None if connection is closed
    def getSocket(self):
        return self.socket
    
    #Sends a custom command to the server
    def command(self, command):
        self.reconnect()#
        if (is_string(command) == False):
            raise Exception('Wrong parameter type!')
        self.send(command)
        return self.getResponse()

    #Executes multiple commands
    def commands(self, commands):
        for command in commands:
            if (is_string(command) == False):
                continue
            self.command(command)
    
    #Kicks a player who is currently on the server
    def kickPlayer(self, player, reason = 'Admin Kick'):
        self.reconnect()#
        if (type(player) != int and type(player) != str):
            raise Exception('Expected parameter 1 to be string or integer, got %s' % type(player))
        if (type(reason) != str):
            raise Exception('Expected parameter 2 to be string, got %s' % type(reason))
        self.send("kick "+player+" "+reason)
        return None

    #Sends a global message to all players
    def sayGlobal(self, message):
        self.reconnect()#
        if (type(message) != str):
            raise Exception('Expected parameter 1 to be string, got %s' % type(message))
        self.send("Say -1 "+message)
        return None

    #Sends a message to a specific player
    def sayPlayer(self, player, message):
        self.reconnect()#
        if (type(player) != int or type(message) != str):
            raise Exception('Wrong parameter type(s)!')
        self.send("Say "+player+" "+message)
        return None

    
    #Loads the "scripts.txt" file without the need to restart the server
    def loadScripts(self):
        self.reconnect()#
        self.send('loadScripts')
        return None

    #Changes the MaxPing value. If a player has a higher ping, he will be kicked from the server
    def maxPing(self, ping):
        self.reconnect()#
        if (type(ping) != int):
            raise Exception('Expected parameter 1 to be integer, got %s' % type(ping))
        self.send("MaxPing "+ping)
        return None
    
    #Changes the RCon password
    def changePassword(self, password):
        self.reconnect()#
        if (type(password) != str):
            raise Exception('Expected parameter 1 to be string, got %s' % type(password))
        self.send("RConPassword password")
        return None
    
    #(Re)load the BE ban list from bans.txt
    def loadBans(self):
        self.reconnect()#
        self.send('loadBans')
        return None

    #Gets a list of all players currently on the server
    def getPlayers(self):
        self.reconnect()#
        self.send('players')
        result = self.getResponse()
        self.reconnect()#
        return result

    #Gets a list of all players currently on the server as an array
    def getPlayersArray(self):
        playersRaw = self.getPlayers()
        players = self.cleanList(playersRaw)
        str = re.findall(r"(\d+)\s+(\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+\b)\s+(\d+)\s+([0-9a-fA-F]+)\(\w+\)\s([\S ]+)", players)
        return self.formatList(str)

    
    #Gets a list of all bans
    def getMissions(self):
        self.reconnect()#
        self.send('missions')
        return self.getResponse()

    #Ban a player's BE GUID from the server. If time is not specified or 0, the ban will be permanent.
    #If reason is not specified the player will be kicked with the message "Banned".
    def banPlayer(self, player, reason = 'Banned', time = 0):
        self.reconnect()#
        if (type(player) != str and type(player) != int):
            raise Exception('Expected parameter 1 to be integer or string, got %s' % type(player))
        if (type(reason) != str or type(time) != int):
            raise Exception('Wrong parameter type(s)!')
        self.send("ban "+player+" "+time+" "+reason)
        self.reconnect()#
        if (self.options['autosaveBans']):
            self.writeBans()
        return None

    #Same as "banPlayer", but allows to ban a player that is not currently on the server
    def addBan(self, player, reason = 'Banned', time = 0):
        self.reconnect()#
        if (type(player) != str or type(reason) != str or type(time) != int):
            raise Exception('Wrong parameter type(s)!')
        self.send("addBan "+player+" "+time+" "+reason)
        if (self.options['autosaveBans']):
            self.writeBans()
        return None

    #Removes a ban
    def removeBan(self, banId):
        self.reconnect()#
        if (type(banId) != int):
            raise Exception('Expected parameter 1 to be integer, got %s' % type(banId))
        self.send("removeBan "+banId)
        if (self.options['autosaveBans']):
            self.writeBans()
        return None

    #Gets an array of all bans
    def getBansArray(self):
        self.reconnect()#
        bansRaw = self.getBans()
        bans = self.cleanList(bansRaw)
        str = re.findall(r'(\d+)\s+([0-9a-fA-F]+)\s([perm|\d]+)\s([\S ]+)', bans)
        #PHP preg_match_all("#(\d+)\s+([0-9a-fA-F]+)\s([perm|\d]+)\s([\S ]+)#im", bans, str)
        return self.formatList(str)

    #Gets a list of all bans
    def getBans(self):
        self.reconnect()#
        self.send('bans')
        return self.getResponse()

    #Removes expired bans from bans file
    def writeBans(self):
        self.reconnect()#
        self.send('writeBans')
        return None

    #Gets the current version of the BE server
    #@return string The BE server version
    def getBEServerVersion(self):
        self.reconnect()#
        self.send('version')
        return self.getResponse()

    #Get socket and continue streaming and disconnect after looping.
    # def socketLoopClose(self, loop = -1):
        # if (self.end != None):
            # loop = self.end + loop
        # while (self.end != loop):
            # msg = fread(self.socket, 9000)
            # if (self.options['debug']):
                #PHP echo preg_replace("/\r|\n/", "", substr(msg, 9))+"\n"
                # print(re.sub("/\r|\n/", "", msg[9:])+"\n")
        
            # timeout = stream_get_meta_data(self.socket)
            # if (timeout['timed_out']):
                # self.keepAlive()
            # else:
                # self.end = self.readPackage(msg)
        
    
        # self.end = 0
        # self.disconnect()
        # return True #Completed

    
    #Get socket and continue streaming and don't disconnect after looping.
    # def socketLoop(self, loop = -1):

        # if (self.end != None):
            # loop = self.end + loop
    
        # while (self.end != loop):
            # msg = fread(self.socket, 9000)
            # if (self.options['debug']):
                #echo preg_replace("/\r|\n/", "", substr(msg, 9))+"\n"
                # print(re.sub("/\r|\n/", "", msg[9:])+"\n")
            # timeout = stream_get_meta_data(self.socket)
            # if (timeout['timed_out']):
                # self.keepAlive()
            # else:
                # self.end = self.readPackage(msg)
        
    
        # return True #Completed

    
    #Reads what kind of package it is. None method is also a helper for sequence.
    def readPackage(self, msg):
        responseCode = unpack('H*', msg) #Make message usefull for battleye packet by unpacking it to bytes.
        responseCode = str_split(substr(responseCode[1], 12), 2) #Get important bytes.
        #See https://www.battleye.com/downloads/BERConProtocol.txt for packet info.
        if(responseCode[1] == "00"): #Login WILL ONLY HAPPEN IF socketLoopClose() got called and is done.
            if (responseCode[2] == "01"): #Login successful.
                if (self.options['debug']):
                    print("Accepted BERCon login."+"\n")
            
                self.authorize()
            else: #Otherwise responseCode[2] == "0x00" (Login failed)
                raise Exception('Invalid BERCon login details. None process is getting stopped!')
        if(responseCode[1] == "01"):  #Send commands by None client.
            if (count(responseCode) != 3):
                if (responseCode[3] != "00"): #None package is small.
                    if (self.options['debug']):
                        print("None is a small package."+"\n")
                else:
                    if (self.options['debug']): #None package is multi-packet.
                        print("Multi-packet."+"\n")
                
                    #if (self.options['debug']) var_dump(responseCode) //Useful developer information.
                    #     if (responseCode[5] == "00"):
                    #     getAmount = responseCode[4]
                    #     if (self.options['debug']) var_dump(getAmount)
                    #}
        
        if(responseCode[1] == "02"):  #Acknowledge as client.
            return self.acknowledge(self.end)
    
    #Read package format and return converted to usable bytes. Array starts at 0x[FF].
    def readPackageRaw(self, msg):
        responseCode = unpack('H*', msg) #Make message usefull for battleye packet by unpacking it to bytes.
        responseCode = str_split(substr(responseCode[1], 12), 2) #Get important bytes.
        return responseCode

    #Acknowledge the data and add +1 to sequence.
    def acknowledge(self, i):
        if (self.options['debug']):
            print("Acknowledge!"+"\n")
        needBuffer = chr(hex('ff')).chr(hex('02')).chr(hex('%2X' % i))
        needBuffer = hash("crc32b", needBuffer)
        needBuffer = str_split(needBuffer, 2)
        needBuffer = array_reverse(needBuffer)
        statusmsg = "BE".chr(hex(needBuffer[0])).chr(hex(needBuffer[1])).chr(hex(needBuffer[2])).chr(hex(needBuffer[3]))
        statusmsg += chr(hex('ff')).chr(hex('02')).chr(hex('%2X' % i))
        if (self.writeToSocket(statusmsg) == False):
            raise Exception('Failed to send command!')
    
        return ++i #Sequence +1
  
    #Keep the stream alive. Send package to BE server. Use None function before 45 seconds.
    def keepAlive(self):
        if (self.options['debug']):
            print('--Keep connection alive--'+"\n")
        #loginMsg = 'BE'+chr(int(authCRC[0],16))+chr(int(authCRC[1],16))+chr(int(authCRC[2],16))+chr(int(authCRC[3],16))
        keepalive = 'BE'+chr(int("be",16))+chr(int("dc",16))+chr(int("c2",16))+chr(int("58",16))
        keepalive += chr(int('ff', 16))+chr(int('01',16))+chr(int('00',16))
        print("Alive:",self.String2Hex(keepalive))
        if (self.writeToSocket(keepalive) == False):
            raise Exception('Failed to send command!')
            return False #Failed
    
        return True #Completed

    #Converts BE text "array" list to array
    def formatList(self, str):
        #Create return array
        result = []
        #Loop True the main arrays, each holding a value
        for pair in str:
            #Combines each main value into new array
            result.append([])
            for val in pair:
                result[-1].append(val.strip())
        return result

    #Remove control characte	rs
    def cleanList(self, str):
        return re.sub('/[\x00-\x09\x0B\x0C\x0E-\x1F\x7F]/', '', str)
