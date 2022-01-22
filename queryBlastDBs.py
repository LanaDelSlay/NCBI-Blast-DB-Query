from ftplib import FTP
import re
import blastDatabase
import sys
from datetime import datetime

arguments = (sys.argv)

## Show each individual file
## Sort by total size
## Sort by most recently updated DBs
showEachFile = False
sortBySize = False
sortByDate = False

dataSizes = {'Bytes', 'KBs', 'MBs', 'GBs'}
ftp = FTP('ftp.ncbi.nlm.nih.gov')
ftp.login()
ftp.cwd('blast/db')
eachDatabasePiece = [] #

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

    if argument == "show_each_db_segment":
        showEachFile == True
    elif argument == "sort_size":
        sortBySize = True
        break
    elif argument == "sort_date":
        sortByDate == True


ftp.retrlines('LIST', lambda block: listLineCallback(block, showEachFile))
totalList = getListTotal(eachDatabasePiece)
if sortBySize:
 print("SIZE SORT")
 print("-"*20)
 totalList.sort(key=biggestSize)
 for items in totalList:
     print(items.toString())

if sortByDate:
    print("DATE SORT")
    print("-" * 20)
    totalList.sort(key=latestUpdate,reverse=True)
    for items in totalList:
        print(items.toString())
