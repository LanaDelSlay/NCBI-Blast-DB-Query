import urllib.request as request
from contextlib import closing
from datetime import datetime
from ftplib import FTP
import blastDatabase
import shutil
import sys
import re
import os

arguments = (sys.argv)

## Show each individual file --show_each_db_segment
## Show each usable DB hosted by NCBI --show_db
## Sort by total size --sort_size
## Sort by most recently updated DBs --sort_date
## Download DBs by running --dl_db human_genome | For a full list of downloadable DB do --show_db

showEachFile = False
showDBNames = False
sortBySize = False
sortByDate = False

ftp = FTP('ftp.ncbi.nlm.nih.gov')
ftp.login()
ftp.cwd('blast/db')
eachDatabasePiece = [] #

def countSegments(list, databaseName):
    count = 0
    for item in list:
        if item.name.startswith(databaseName):
            count = count + 1
    return count

def downloadDataBase(databaseName):
    ## Need to do a free size check and make sure there's enough space.
    segmentsOfDB = countSegments(eachDatabasePiece, databaseName)
    path = databaseName + "_files"
    os.makedirs(path, exist_ok=True)
    if segmentsOfDB <= 1:
        file = open(path + os.path.sep + databaseName, 'wb')
        ftp.retrbinary("RETR " + databaseName, file.write)
    else:
        for i in range(segmentsOfDB):
            dataBaseSeg = databaseName + "." + "{:02d}".format(i) + ".tar.gz"
            local_filename = os.path.join(path + os.path.sep, dataBaseSeg)
            file = open(local_filename, 'wb')
            print('Downloading ' + dataBaseSeg)
            ftp.retrbinary('RETR ' + dataBaseSeg, file.write)
    ftp.quit()

def getSizeInUnits(size):
    if size > 1024:
        fileSizeKBs = size / 1024
        if fileSizeKBs > 1024:
            fileSizeMBs = fileSizeKBs / 1024
            if fileSizeMBs > 1024:
                fileSizeGBs = fileSizeMBs / 1024
                if fileSizeGBs > 1024:
                    fileSizeTBs = fileSizeGBs / 1024
                    return round(fileSizeTBs, 3) + "TBs"
                else:
                    return str(round(fileSizeGBs, 3)) + "GBs"
            else:
                return str(round(fileSizeMBs, 3)) + "MBs"
        else:
            return str(round(fileSizeKBs, 3)) + "KBs"
    else:
        return size + "Bytes"

def getTotalSize(list, name):
    totalSize = 0
    iteration = 0

    for i in list:
        x = re.sub("\.\d{1,3}", "", i.name) # Remove the numbers at the end of each download
        if x == name:
            totalSize = totalSize + i.sizeInBytes
        iteration = iteration + 1
    return totalSize

def listLineCallback(line, printEachItem = False):
    if line.endswith('.md5') or line.endswith('.json') or line.endswith('README'):
        return # Ignores md5 files
    if line.startswith('dr-xr-xr-x'):
        return # Ignore the other weird files
    msg = line.removeprefix('-r--r--r--   1 ftp      anonymous').removesuffix('.tar.gz').strip();
    fileSizeBytes = list(map(int, re.findall(r'\d+', msg)))[0] # Get all numbers in str, we only need the first one.
    sizeStr = getSizeInUnits(fileSizeBytes)
    restOfStr = msg[len(str(fileSizeBytes)): len(msg)].replace("  ", " ") ## Odd formatting from ftp with random double space
    date = re.search(r'\w{3} \d+ ?\d{2}?:?\d+', restOfStr).group()
    name = restOfStr[len(date)+2:len(restOfStr)].strip()
    if printEachItem:
        print("Name: {0:30} Size: {1:14} Last Update: {2}".format(name, sizeStr, date));
    thisDB = blastDatabase.database(name, sizeStr, date, fileSizeBytes)
    eachDatabasePiece.append(thisDB)

def getUniqueNames(list):
    uniqueNames = []
    lastName = ""
    for item in list:
        nameWithOutNums = re.sub("\.\d{1,3}", "", item.name) # Remove the numbers at the end of each download
        if nameWithOutNums != lastName:
            uniqueNames.append(nameWithOutNums)
        lastName = nameWithOutNums
    return uniqueNames

def getLastUpdate(list, name):
    for item in list:
        itemName = re.sub("\.\d{1,3}", "", item.name) # Remove the numbers at the end of each download
        if itemName == name:
            return item.lastUpdate

def getListTotal(list):
    totalsList = []
    names = getUniqueNames(list)
    for name in names:
        size = getTotalSize(list, name)
        lastUpdate = getLastUpdate(list, name)
        thisDB = blastDatabase.database(name, getSizeInUnits(size), lastUpdate, size)
        totalsList.append(thisDB)
    return totalsList

def latestUpdate(database):
    datetime_object = None
    try:
        datetime_object = datetime.strptime(database.lastUpdate, '%b %d %H:%M')
        datetime_object = datetime_object.replace(datetime.today().year)
        if datetime.now() < datetime_object: # Dates dont report the year it was uploaded until it's been a year, so this will check if the dates in the future and if so decrement.
           datetime_object = datetime_object.replace(datetime.now().year - 1)
    except ValueError:
        pass
    try:
        datetime_object = datetime.strptime(database.lastUpdate, '%b %d %Y')
        if datetime_object > datetime.today():
            datetime_object.replace(2021)
    except ValueError:
        pass
    return (datetime_object)

def biggestSize(database):
    return database.sizeInBytes

for argument in arguments:
    argumentCount = 1
    argument = argument.replace("--", "")
    argument = argument.lower()
    if argument == "show_each_db_segment":
        showEachFile = True
    elif argument == "sort_size":
        sortBySize = True
    elif argument == "sort_date":
        sortByDate = True
    elif argument == "show_db" or argument == "show_dbs":
        showDBNames = True
    elif argument == "dl_db":
        downloadDataBase(arguments[argumentCount + 1])
    argumentCount = argumentCount + 1

ftp.retrlines('LIST', lambda block: listLineCallback(block, showEachFile))
totalList = getListTotal(eachDatabasePiece)

if sortBySize:
 print()
 print("-" * 20)
 print("SIZE SORT")
 print("-"*20)
 totalList.sort(key=biggestSize, reverse=True)
 for items in totalList:
     print(items.toString())
 print()

if sortByDate:
    print()
    print("-" * 20)
    print("DATE SORT")
    print("-" * 20)
    totalList.sort(key=latestUpdate,reverse=True)
    for items in totalList:
        print(items.toString())
    print()

if showDBNames:
    print()
    print("-" * 20)
    print("DATABASES")
    print("-" * 20)
    names = getUniqueNames(totalList)
    for name in names:
        print(name)

if len(arguments) <= 1:
    print("Run this with these commands to sort and display the DBs.")
    print("")
    print("--show_each_db_segment  This will show each file making up a DB and it's relevant info")
    print("--sort_size  This will sort each database by it's total size")
    print("--sort_date This will sort by most recent update and print them out")
    print("--show_db This will show all available DBs for BLAST hosted by NCBI")
    print("Example usage: python3 queryBlastDBs.py --show_each_db_segment --sort_size")
    downloadDataBase("human_genome")

