from ftplib import FTP
import re

ftp = FTP('ftp.ncbi.nlm.nih.gov')
ftp.login()
ftp.cwd('blast/db')

def giveSize(size):
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

def listLineCallback(line):
    if line.endswith('.md5') or line.endswith('.json') or line.endswith('README'):
        return # Ignores md5 files
    if line.startswith('dr-xr-xr-x'):
        return # Ignore the other weird files
    msg = line.removeprefix('-r--r--r--   1 ftp      anonymous').removesuffix('.tar.gz').strip();
    fileSizeBytes = list(map(int, re.findall(r'\d+', msg)))[0] # Get all numbers in str, we only need the first one.
    sizeStr = giveSize(fileSizeBytes)
    restOfStr = msg[len(str(fileSizeBytes)): len(msg)].replace("  ", " ") ## Odd formatting from ftp with random double space
    date = re.search(r'\w{3} \d+ ?\d{2}?:?\d+', restOfStr).group()
    name = restOfStr[len(date)+2:len(restOfStr)].strip()
    print("Name: {0:30} Size: {1:14} Last Update: {2}".format(name, sizeStr, date));

ftp.retrlines('LIST', listLineCallback )