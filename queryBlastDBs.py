from datetime import datetime
from ftplib import FTP
import blastDatabase
import difflib
import wget
import sys
import re
import os

# Show each individual file --show_each_db_segment
# Show each usable DB hosted by NCBI --show_db
# Sort by total size --sort_size
# Sort by most recently updated DBs --sort_date
# Download DBs by running --dl_db human_genome | For a full list of downloadable DB do --show_db

def count_segments(segment_list, database_name):
    count = 0
    for item in segment_list:
        if item.name.startswith(database_name):
            count = count + 1
    return count

def dl_database(database_name):
    if is_valid_db(list, database_name):
        base_URL = "ftp://ftp.ncbi.nlm.nih.gov/blast/db/"
        segments_of_db = count_segments(each_database_piece, database_name)
        path = database_name + "_files"
        os.makedirs(path, exist_ok=True)
        if segments_of_db <= 1:
            path = database_name + "_files"
            url = base_URL + database_name + ".tar.gz"
            wget.download(url, path, bar=bar_progress)
        else:
            for i in range(segments_of_db):
                path = database_name + "_files"
                url = base_URL + database_name + "." + "{:02d}".format(i) + ".tar.gz"
                sys.stdout.flush()
                print('DLing: {}.{:02d} [Segment {} of {}]'.format(database_name, i, i + 1, segments_of_db))
                wget.download(url, path, bar=bar_progress)

def is_valid_db(collapsed_list, database_name):
    for item in collapsed_list:
        if(item.name == database_name):
            return True
    find_closest_match(collapsed_list, database_name)
    return False

def find_closest_match(collapsed_list, database_name):
    name_list = []
    for item in collapsed_list:
        name_list.append(item.name)
    matches = difflib.get_close_matches(database_name, name_list)
    print('Did you mean: ')
    print('\n'.join('{}: {}'.format(*k) for k in enumerate(matches)))

def bar_progress(current, total, width=80):
    progress_message = "Downloading: %d%% [%d / %d] bytes" % (current / total * 100, current, total)
    # Don't use print() as it will print in new line every time.
    sys.stdout.write("\r" + progress_message)
    sys.stdout.flush()

def get_size_in_units(size):
    if size > 1024:
        file_size_kbs = size / 1024
        if file_size_kbs > 1024:
            file_size_mbs = file_size_kbs / 1024
            if file_size_mbs > 1024:
                file_size_gbs = file_size_mbs / 1024
                if file_size_gbs > 1024:
                    file_size_tbs = file_size_gbs / 1024
                    return round(file_size_tbs, 3) + "TBs"
                else:
                    return str(round(file_size_gbs, 3)) + "GBs"
            else:
                return str(round(file_size_mbs, 3)) + "MBs"
        else:
            return str(round(file_size_kbs, 3)) + "KBs"
    else:
        return size + "Bytes"

def get_total_size(segment_list, database_name):
    total_size = 0
    iteration = 0

    for i in segment_list:
        x = re.sub("\.\d{1,3}", "", i.name) # Remove the numbers at the end of each download
        if x == database_name:
            total_size = total_size + i.sizeInBytes
        iteration = iteration + 1
    return total_size

def list_line_callback(line, print_each_item = False):
    if line.endswith('.md5') or line.endswith('.json') or line.endswith('README'):
        return # Ignores md5 files
    if line.startswith('dr-xr-xr-x'):
        return # Ignore the other weird files
    msg = line.removeprefix('-r--r--r--   1 ftp      anonymous').removesuffix('.tar.gz').strip();
    file_size_bytes = list(map(int, re.findall(r'\d+', msg)))[0] # Get all numbers in str, we only need the first one.
    size_str = get_size_in_units(file_size_bytes)
    rest_of_str = msg[len(str(file_size_bytes)): len(msg)].replace("  ", " ") ## Odd formatting from ftp with random double space
    date = re.search(r'\w{3} \d+ ?\d{2}?:?\d+', rest_of_str).group()
    db_name = rest_of_str[len(date)+2:len(rest_of_str)].strip()
    if print_each_item:
        print("Name: {0:30} Size: {1:14} Last Update: {2}".format(db_name, size_str, date));
    this_db = blastDatabase.database(db_name, size_str, date, file_size_bytes)
    each_database_piece.append(this_db)

def get_unique_names(collapsed_list):
    unique_names = []
    last_name = ""
    for item in collapsed_list:
        name_with_out_nums = re.sub("\.\d{1,3}", "", item.name) # Remove the numbers at the end of each download
        if name_with_out_nums != last_name:
            unique_names.append(name_with_out_nums)
        last_name = name_with_out_nums
    return unique_names

def get_last_update(collapsed_list, database_name):
    for item in collapsed_list:
        item_name = re.sub("\.\d{1,3}", "", item.name)  # Remove the numbers at the end of each download
        if item_name == database_name:
            return item.lastUpdate

def get_list_total(segment_list):
    totals_list = []
    db_names = get_unique_names(segment_list)
    for db_name in db_names:
        size = get_total_size(segment_list, db_name)
        lastUpdate = get_last_update(segment_list, db_name)
        thisDB = blastDatabase.database(db_name, get_size_in_units(size), lastUpdate, size)
        totals_list.append(thisDB)
    return totals_list

def sort_by_latest_update(database):
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

def sort_by_biggest_size(database):
    return database.sizeInBytes


# each_database_piece Contains each individual DB segments
# total_list is a collapsed list with size name and date all turned into one object representing each DB.
show_each_file = False
show_db_names = False
sort_by_size = False
sort_by_date = False
arguments = sys.argv
ftp = FTP('ftp.ncbi.nlm.nih.gov')
ftp.login()
ftp.cwd('blast/db')
each_database_piece = []

for argument in arguments:

    argument_count = 1
    argument = argument.replace("--", "")
    argument = argument.lower()
    if argument == "show_each_db_segment":
        show_each_file = True
    elif argument == "sort_size":
        sort_by_size = True
    elif argument == "sort_date":
        sort_by_date = True
    elif argument == "show_db" or argument == "show_dbs":
        show_db_names = True
    elif argument == "dl_db":
        dl_database(arguments[argument_count + 1])
    argument_count = argument_count + 1

ftp.retrlines('LIST', lambda block: list_line_callback(block, show_each_file))
total_list = get_list_total(each_database_piece)

if sort_by_size:
    print()
    print("-" * 20)
    print("SIZE SORT")
    print("-"*20)
    total_list.sort(key=sort_by_biggest_size, reverse=True)
    for items in total_list:
        print(items.toString())
    print()

if sort_by_date:
    print()
    print("-" * 20)
    print("DATE SORT")
    print("-" * 20)
    total_list.sort(key=sort_by_latest_update, reverse=True)
    for items in total_list:
        print(items.toString())
    print()

if show_db_names:
    print()
    print("-" * 20)
    print("DATABASES")
    print("-" * 20)
    names = get_unique_names(total_list)
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
