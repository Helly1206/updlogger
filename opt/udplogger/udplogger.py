#!/usr/bin/python3

# -*- coding: utf-8 -*-
#########################################################
# SERVICE : mqttlogger.py                               #
#           Simple logger of MQTT traffic               #
#           To be used for debugging or visualizing     #
#           I. Helwegen 2022                            #
#########################################################

####################### IMPORTS #########################
import sys
import os
import signal
import shutil
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
from uuid import getnode
from datetime import datetime
import socket
from select import select

#########################################################

####################### GLOBALS #########################
VERSION      = "0.80"
XML_FILENAME = "udplogger.xml"
ENCODING     = 'utf-8'
LOG_EXT      = "_log.txt"
MAXFILES     = 8
#########################################################

###################### FUNCTIONS ########################

#########################################################
# Class : database                                      #
#########################################################
class database(object):
    def __init__(self):
        self.db = {}
        if not self.getXMLpath(False):
            # only create xml if super user, otherwise keep empty
            self.createXML()
            self.getXML()
        else:
            self.getXML()

    def __del__(self):
        del self.db
        self.db = {}

    def __call__(self):
        return self.db

    def update(self):
        self.updateXML()

    def reload(self):
        del self.db
        self.db = {}
        self.getXML()

    def bl(self, val):
        retval = False
        try:
            f = float(val)
            if f > 0:
                retval = True
        except:
            if val.lower() == "true" or val.lower() == "yes" or val.lower() == "1":
                retval = True
        return retval

################## INTERNAL FUNCTIONS ###################

    def gettype(self, text, txtype = True):
        try:
            retval = int(text)
        except:
            try:
                retval = float(text)
            except:
                if text:
                    if text.lower() == "false":
                        retval = False
                    elif text.lower() == "true":
                        retval = True
                    elif txtype:
                        retval = text
                    else:
                        retval = ""
                else:
                    retval = ""

        return retval

    def settype(self, element):
        retval = ""
        if type(element) == bool:
            if element:
                retval = "true"
            else:
                retval = "false"
        elif element != None:
            retval = str(element)

        return retval

    def getXML(self):
        XMLpath = self.getXMLpath()
        try:
            tree = ET.parse(XMLpath)
            root = tree.getroot()
            self.db = self.parseKids(root, True)
        except Exception as e:
            print("Error parsing xml file")
            print("Check XML file syntax for errors")
            print(e)
            exit(1)

    def parseKids(self, item, isRoot = False):
        db = {}
        if self.hasKids(item):
            for kid in item:
                if self.hasKids(kid):
                    db[kid.tag] = self.parseKids(kid)
                else:
                    db.update(self.parseKids(kid))
        elif not isRoot:
            db[item.tag] = self.gettype(item.text)
        return db

    def hasKids(self, item):
        retval = False
        for kid in item:
            retval = True
            break
        return retval

    def updateXML(self):
        db = ET.Element('logger')
        pcomment = self.getXMLcomment("")
        if pcomment:
            comment = ET.Comment(pcomment)
            db.append(comment)
        self.buildXML(db, self.db)

        XMLpath = self.getXMLpath(dowrite = True)

        with open(XMLpath, "w") as xml_file:
            xml_file.write(self.prettify(db))

    def buildXML(self, xmltree, item):
        if isinstance(item, dict):
            for key, value in item.items():
                kid = ET.SubElement(xmltree, key)
                self.buildXML(kid, value)
        else:
            xmltree.text = self.settype(item)

    def createXML(self):
        print("Creating new XML file")
        db = ET.Element('logger')
        comment = ET.Comment("This XML file describes the server to log from.\n"
        "            <logger> Main element, do not change name\n"
        "                <loggername> Name of the logger, change if required\n"
        "                   <ip> IP-address of UDP server (0.0.0.0 for all ip)\n"
        "                   <port> UDP port\n"
        "                   <time> true or false add time information\n"
        "                   <folder> Path to store logfiles (only used in daemon mode)\n"
        "                   <maxsize> Maximum file size in bytes\n")
        db.append(comment)
        lgr = ET.SubElement(db, "mylogger")
        ip = ET.SubElement(lgr, "ip")
        ip.text = "0.0.0.0"
        port = ET.SubElement(lgr, "port")
        port.text = "6309"
        logtime = ET.SubElement(lgr, "time")
        logtime.text = "true"
        folder = ET.SubElement(lgr, "folder")
        folder.text = "."
        maxsize = ET.SubElement(lgr, "maxsize")
        maxsize.text = "1000000"
        XMLpath = self.getNewXMLpath()

        with open(XMLpath, "w") as xml_file:
            xml_file.write(self.prettify(db))

    def getXMLcomment(self, tag):
        comment = ""
        XMLpath = self.getXMLpath()
        with open(XMLpath, 'r') as xml_file:
            content = xml_file.read()
            if tag:
                xmltag = "<{}>".format(tag)
                xmlend = "</{}>".format(tag)
                begin = content.find(xmltag)
                end = content.find(xmlend)
                content = content[begin:end]
            cmttag = "<!--"
            cmtend = "-->"
            begin = content.find(cmttag)
            end = content.find(cmtend)
            if (begin > -1) and (end > -1):
                comment = content[begin+len(cmttag):end]
        return comment

    def prettify(self, elem):
        """Return a pretty-printed XML string for the Element.
        """
        rough_string = ET.tostring(elem, ENCODING)
        reparsed = parseString(rough_string)
        return reparsed.toprettyxml(indent="\t").replace('<?xml version="1.0" ?>','<?xml version="1.0" encoding="%s"?>' % ENCODING)

    def getXMLpath(self, doexit = True, dowrite = False):
        etcpath = "/etc/"
        XMLpath = ""
        # first look in etc
        if os.path.isfile(os.path.join(etcpath,XML_FILENAME)):
            XMLpath = os.path.join(etcpath,XML_FILENAME)
            if dowrite and not os.access(XMLpath, os.W_OK):
                print("No valid writable XML file location found")
                print("XML file cannot be written, please run as super user")
                if doexit:
                    exit(1)
        else: # Only allow etc location
            print("No XML file found")
            if doexit:
                exit(1)
        return XMLpath

    def getNewXMLpath(self):
        etcpath = "/etc/"
        XMLpath = ""
        # first look in etc
        if os.path.exists(etcpath):
            if os.access(etcpath, os.W_OK):
                XMLpath = os.path.join(etcpath,XML_FILENAME)
        if (not XMLpath):
            print("No valid writable XML file location found")
            print("XML file cannot be created, please run as super user")
            exit(1)
        return XMLpath


#########################################################

#########################################################
# Class : udplogger                                     #
#########################################################
class udplogger(object):
    def __init__(self):
        self.name         = ""
        self.isdaemon     = False
        self.debug        = False
        self.timeout      = 1
        self.bufsize      = 1024
        self.servers      = []
        self.items        = []
        signal.signal(signal.SIGINT, self.exit_app)
        signal.signal(signal.SIGTERM, self.exit_app)
        self.kill = False

    def __del__(self):
        pass

    def __str__(self):
        return "{}: logging of UDP traffic".format(self.name)

    def __repr__(self):
        return self.__str__()

    def run(self, argv):
        if len(os.path.split(argv[0])) > 1:
            self.name = os.path.split(argv[0])[1]
        else:
            self.name = argv[0]

        self.db = database()

        index = 0
        for arg in argv:
            if arg[0] == "-":
                if arg == "-h" or arg == "--help":
                    self.printHelp()
                    exit()
                elif arg == "-v" or arg == "--version":
                    print(self)
                    print("Version: {}".format(VERSION))
                    exit()
                elif arg == "-d" or arg == "--debug":
                    self.debug = True
                    del argv[index]
                elif arg == "-s" or arg == "--service":
                    self.isdaemon = True
                    del argv[index]
                else:
                    self.parseError(arg)
            index += 1
        if len(argv) < 2:
            self.daemon()
        else:
            self.parseError(argv[1])

    def printHelp(self):
        print(self)
        print("Usage:")
        print("    {} {}".format(self.name, "<arguments>"))
        print("        -h, --help    : Display this help")
        print("        -v, --version : Display version")
        print("        -d, --debug   : Debug communication")
        print("        -s, --service : Run as daemon")
        print("        <no arguments>: run as command line")
        print("When running as command line, logging is to stdout")
        print("")

    def parseError(self, opt = ""):
        print(self)
        print("Invalid option entered")
        if opt:
            print(opt)
        print("Enter '{} -h' for help".format(self.name))
        exit(1)

    def daemon(self):
        for key, item in self.db().items():
            item2 = {}
            item2["name"] = key
            if "ip" in item:
                item2["ip"] = item["ip"]
            else:
                item2["ip"] = "0.0.0.0"
            if "port" in item:
                item2["port"] = item["port"]
            else:
                item2["port"] = 6309
            if "folder" in item:
                item2["folder"] = item["folder"]
            else:
                item2["folder"] = "."
            if "time" in item:
                item2["time"] = item["time"]
            else:
                item2["time"] = True
            if "maxsize" in item:
                item2["maxsize"] = item["maxsize"]
            else:
                item2["maxsize"] = 1000000
            item2["size"] = 0
            self.movePath(item2)

            server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet  # UDP
            server.bind(("0.0.0.0", item2["port"]))
            server.setblocking(0)
            self.servers.append(server)
            self.items.append(item2)

        while not self.kill:
            ready = select(self.servers, [], [], self.timeout)
            for sock in ready[0]:
                index = self.servers.index(sock)
                self.onreceive(sock.recvfrom(self.bufsize), self.items[index])

    def exit_app(self, signum, frame):
        print("Terminating ...")
        self.kill = True

    def onreceive(self, buf, item):
        if ((buf[1][0] == item["ip"]) or (item["ip"] == "0.0.0.0")) and (buf[1][1] == item["port"]):
            self.writelog(buf[0].decode('utf-8'), item)

    def writelog(self, buf, item):
        logstr = ""
        if item["time"]:
            now = datetime.now()
            logstr = str(now.timestamp()) + ", "
            logstr += now.strftime("%d-%m-%Y") + ", "
            logstr += now.strftime("%H:%M:%S") + ", "
        logstr += buf + "\n"
        item["size"] += len(logstr)
        try:
            if self.isdaemon:
                with open(self.logPath(item), "a") as f:
                    f.write(logstr)
            else:
                raise Exception("")
        except:
            print(logstr, end = "")
        if (item["maxsize"] > 0) and (item["size"] > item["maxsize"]):
            item["size"] = 0
            self.movePath(item)

    def movePath(self, item):
        if os.path.exists(self.logPath(item)):
            self.copyFile(self.logPath(item))
            os.remove(self.logPath(item)) # move to .1,, .2 etc later)

    def logPath(self, item):
        fname = item["name"] + "_" + item["ip"].replace("/","_") + "_" + str(item["port"]) + LOG_EXT
        return os.path.join(item["folder"], fname)

    def copyFile(self, path):
        for i in range(MAXFILES-1, -1, -1):
            if i == 0:
                cpsrc = path
            else:
                cpsrc = path + "." + str(i)
            cpdst = path + "." + str(i+1)
            try:
                shutil.copyfile(cpsrc, cpdst)
            except:
                pass

######################### MAIN ##########################
if __name__ == "__main__":
    udplogger().run(sys.argv)
