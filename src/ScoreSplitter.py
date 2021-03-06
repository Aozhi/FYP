#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 Eoghan Hynes <eoghan@hyn.es>
#
# Distributed under terms of the MIT license.

"""
    Splits MusicXML by beat into corresponding SPEAC
    directories.

    *** Currently only works on the first SPEAC ID for 
    any beats which have an equal match with multiple IDs

"""

#TODO: Store "destination" of beats along with beats
#TODO: Currently not categorising SPEAC correctly

import SPEACIDs
import os
import lxml.etree as ET
from collections import defaultdict
from optparse import OptionParser

# Setup program flags and descriptions
parser = OptionParser()
parser.add_option("-f", "--file", action="store", dest="filename", help="specify file")
(options, args) = parser.parse_args()

if(options.filename):
    filename = options.filename
else:
    print("Usage: python3 ScoreSplitter.py -f [PATH TO FILE]")
    sys.exit()

# create SPEAC dicts
speacIDList = SPEACIDs.SPEACIDsToList()
#SPEACdict = dict.fromkeys(speacIDList,[])
SPEACdict = {k:[] for k in speacIDList}

def ensureExistance(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    for ID in speacIDList:
        if not os.path.exists(directory+ID+".xml"):
            f = open(directory+ID+".xml","w")
            f.write("<beatlist>\n</beatlist>")
            f.close()


def writeToFile( SPEACdict ):
    directory = os.path.dirname(os.path.realpath(__file__))
    directory += "/../data/SPEAC/"
    ensureExistance(directory)
    speacxml = dict.fromkeys(speacIDList,ET.Element)
    for ID in speacIDList:
        speacxml[ID] = ET.parse(directory+ID+".xml")

    for ID, beatlist in SPEACdict.items():
        root = speacxml[ID].getroot()
        root.set('speacID', ID)

        for beat in beatlist:
            beatElm = ET.Element('beat')
            beatElm.tail = "\n"
            backupin = False
            emptyBeat = False
            for notes in beat:
                if not notes.findall("rest") == []: 
                # ensure there aren't any empty beats
                    emptyBeat = True
                    break
                if notes.findtext("staff") == "2" and not backupin:
                    duration = notes.findtext("duration")
                    if int(duration) > 48: # fixing polyphony
                        backup = ET.fromstring("<backup><duration>"+duration+"</duration></backup>")
                    else:
                        backup = ET.fromstring("<backup><duration>48</duration></backup>")
                    beatElm.append(backup)
                    backupin = True
                beatElm.append(notes)
            if len(beatElm) and not emptyBeat:
                root.append(beatElm)

        speacxml[ID].write(directory+ID+".xml",pretty_print=True)
        del speacxml[ID]


def categorise( measure ):
    beatlist = list(measure.items())
    for beatno, note in beatlist:
        speac = None
        for n in note:
            speac = n.find("speac")
            if speac != None:
            # break early if found
                break
        if speac != None:
            ID = speac.text[:2]
            SPEACdict[ID].append(note)

def groupBeats( measure ):
    """ Groups beats into dictionarys where the beatnumber is the key
    :param measure: the MusicXML measure to be queried
    :type measure: xml.etree.ElementTree.Element
    :returns: a dictonary of beatnumber : notes
    :rtype: defaultdict(list) 
    """
    beatDict = defaultdict(list)
    for note in measure:
        if note.attrib != {}:
            ndict = note.attrib
            if 'beatnumber' in ndict.keys():
                beatDict[ndict['beatnumber']].append(note)
    return beatDict

def split ( filename ):
    tree = ET.parse(filename)

    measureBeats = []
    for measure in tree.findall("./part/measure"):
        measureBeats.append(groupBeats(measure))

    for measure in measureBeats:
        categorise( measure )

    writeToFile(SPEACdict)
    #for ID,notes in SPEACdict.items():
    #    print(ID,notes)

if __name__ == '__main__':
    split( filename )
