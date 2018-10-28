"""
highscores.py - Highscore manipulation functions

July 2018, Lewis Gaul

Highscores are stored separately under filenames representing the settings
which group them. The first line of the file should match the filename, and if
this is not the case (for example if the file is modified) a warning will be
issued - note this is not used for checking validity of the highscores.
Each highscore is stored with a key which is used for checking validity.
"""


import sys
import os
from os.path import join, exists, basename, splitext
import csv
from distutils.version import LooseVersion
from glob import glob
import logging

from minegauler.shared import (ASSERT, highscores_dir, HighscoreSettingsStruct,
    HighscoreStruct)


logger = logging.getLogger(__name__)


# Store all highscores as they're imported in a dictionary of lists, with their
#  keys being the string representation of the settings.
all_highscores = {}
# For example:
# all_highscores = {'diff=b,drag_select=False,per_cell=1': [
#                      {'name':     'anon',     # str, len <= 12
#                       'time':     1234,       # int (ms)
#                       '3bv':      1,          # int
#                       'date':     15/07/18 18:36:38, # str
#                       'flagging': 'NF',       # 'F' or 'NF'
#                       'key':      0,          # int
#                       }]
#                   }
# Store the number of imported highscores from each file to allow for only
#  appending new highscores while they're all stored together.
num_imported_highscores = {}
# For example:
# num_imported_highscores = {'diff=b,drag_select=False,per_cell=1': 10}


#@@@ REMEMBER TO CHANGE THIS FOR OFFICIAL RELEASES BEFORE ENCRYPTING THE CODE
def enchs(s, h):
    """
    Encode highscore into a key.
    Arguments:
      s (HighscoreSettingsStruct)
        Settings for the highscore.
      h (HighscoreStruct)
        Highscore.
    Return:
      Key for the highscore.
    """
    return int(
        sum([412.12 * ord(c) for c in s.to_string()]) +
        sum([688.99 * ord(c) for c in h['name']]) +
        200.34 * h['time'] +
        111.67 * h['3bv']
        )


def read_highscores(settings, fpath):
    if not exists(fpath):
        logger.info("Highscores file not found: %s", fpath)
        return []
    with open(fpath, 'r') as f:
        reader = csv.reader(f, escapechar='\\', delimiter='\t')
        # The first line should contain the headers, giving the key order.
        try:
            hscore_keys = next(reader)
        except StopIteration:
            # If file is empty, delete it so that it can be created properly.
            logger.warn("Highscores file seems to be empty - deleting")
            f.close()
            os.rename(fpath, fpath[:-4] + '_archive.csv')
            return []
            
        if hscore_keys != HighscoreStruct.elements:
            logger.error("Unexpected highscore keys in file: %s", hscore_keys)
            logger.info("Attempting to continue reading highscore file")
            hscore_keys = HighscoreStruct.elements
        invalid_rows = 0
        highscores = []
        for i, row in enumerate(reader):                    
            try:
                h = {key: row[j] for j, key in enumerate(hscore_keys)}
                for key in ['time', '3bv', 'key']:
                    h[key] = int(h[key])
                h = HighscoreStruct(**h)
            except (ValueError, IndexError):
                logger.error("Invalid row %d: %s", i, row)
                invalid_rows += 1
                if invalid_rows < 10:
                    logger.info("Attempting to continue reading highscore file")
                    continue
                else:
                    logger.info("%d invalid rows, giving up reading file",
                                invalid_rows)
                    break
                    
            if True: #@@@ enchs(settings, h) == h['key']:
                if h['name']:
                    highscores.append(h)
            else:
                logger.warn("Invalid key for highscore: %s", h)
    return highscores


def get_highscores(settings):
    # If the file has already been read no need to read again, and there may
    #  also be some new highscores which are stored in all_highscores and yet to
    #  be saved to the file.
    if settings.to_string() not in all_highscores:
        fpath = join(highscores_dir, f'{settings.to_string()}.csv')
        hscores = read_highscores(settings, fpath)
        all_highscores[settings.to_string()] = hscores
        num_imported_highscores[settings.to_string()] = len(hscores)
    return hscores


def write_highscores(settings):
    """
    If file doesn't exist for these settings create it. Append any new
    highscores to the file.
    """
    fpath = join(highscores_dir, f'{settings.to_string()}.csv')
    if not exists(fpath):
        # Highscores file lost (deleted?) - save all
        logger.info("Creating highscores file: %s", fpath)
        num_imported_highscores[settings.to_string()] = 0
        with open(fpath, 'w', newline='') as f:
            # Write the headings, giving the key order.
            writer = csv.DictWriter(f, HighscoreStruct.elements,
                                    quoting=csv.QUOTE_NONE,
                                    escapechar='\\',
                                    delimiter='\t')
            writer.writeheader()
    # Append new highscores to file.
    with open(fpath, 'a', newline='') as f:
        writer = csv.DictWriter(f, HighscoreStruct.elements,
                                quoting=csv.QUOTE_NONE,
                                escapechar='\\',
                                delimiter='\t')
        new_hscores_index = num_imported_highscores[settings.to_string()]
        new_hscores = all_highscores[settings.to_string()][new_hscores_index:]
        writer.writerows(new_hscores)
        num_imported_highscores[settings.to_string()] = len(
                                           all_highscores[settings.to_string()])


def save_all_highscores():
    for key in all_highscores:
        write_highscores(HighscoreSettingsStruct.from_string(key))


def filter_and_sort(highscore_list, sort_by, filters):
    out_list = []
    filters = {k: f for k, f in filters.items() if f}
    for h in highscore_list:
        all_pass = True
        for key, f in filters.items():
            if h[key].lower() != f.lower():
                all_pass = False
                break
        if all_pass:
            # All filters satisfied.
            out_list.append(h)
    # Sort first by either time or 3bv/s, then by 3bv if there's a tie
    #  (higher 3bv higher for equal time, lower for equal 3bv/s).
    if sort_by == 'time':
        out_list.sort(key=lambda h:(h['time'], -h['3bv']))
    elif sort_by == '3bv/s':
        out_list.sort(key=lambda h:(h.get_3bvps(), -h['3bv']), reverse=True)
    if 'name' not in filters:
        # If no name filter, only include best highscore for each name.
        names = []
        i = 0
        while i < len(out_list):
            h = out_list[i]
            name = h['name'].lower()
            if name in names:
                out_list.pop(i)
            else:
                names.append(name)
                i += 1
    return out_list


def get_hscore_position(hscore, settings, filters={}, cut_off=5):
    #@@@
    settings = settings_to_str(settings)
    highscores = []
    filters = {k: v for k, v in filters.items() if v}
    for h in all_highscores[settings]:
        all_pass = True
        for key, f in filters.items():
            if h[key].lower() != f.lower():
                all_pass = False
                break
        if all_pass:
            highscores.append(h) #all filters satisfied
    highscores.sort(key=lambda h: (h.time, -h._3bv))
    if hscore in highscores[:cut_off]:
        return 'time'
    highscores.sort(key=lambda h: (h.get_3bvps(), -h._3bv), reverse=True)
    if hscore in highscores[:cut_off]:
        return '3bv/s'
    return None


def include_old_hscores(direc, version, frozen=True):
    """
    Convert and add hscores in the new format. Assumes the data file exists
    in direc.
    """
    version = LooseVersion(version)
    if version < '1.1.2':
        # Used to use eval. Support removed.
        raise ValueError("Only supported for versions of at least 1.1.2")
    ASSERT(HighscoreSettingsStruct.elements == ['diff', 'drag_select', 'per_cell'])
    ASSERT(HighscoreStruct.elements == ['name', 'time', '3bv', 'date', 'flagging', 'key'])
    added = 0
    if '1.1' < version < '1.2':
        import json
        if frozen:
            path = join(direc, 'files', 'data.txt')
        else:
            path = join(direc, 'data', 'data.txt')
        with open(path, 'r') as f: #catch FileNotFoundError
            old_data = json.load(f)
        for h in old_data:
            if (h['lives'] > 1 or h['per_cell'] > 3 or h['detection'] != 1
                or h['distance_to'] != False or not h['name']
                or ('proportion' in h and h['proportion'] < 1)):
                continue #don't include
            settings = {k: h[k] for k in HighscoreSettingsStruct.elements}
            # new_h = {k: h[k] for k in HighscoreStruct.elements}
            new_h['time'] = int(1000 * float(h['time'])) #str (s) to int (ms)
            new_h['3bv'] = h['3bv']
            new_h['drag_select'] = bool(h['drag_select'])
            new_h['date'] = int(h['date'])
            new_h['flagging'] = 'F' if h['flagging'] else 'NF'
            new_h['key'] = enchs(settings, new_h) #no check
            hscores_list = get_highscores(settings)
            if new_h not in hscores_list:
                hscores_list.append(new_h)
                added += 1
    elif '1.2' <= version < '2.0':
        import json
        if frozen:
            path = join(direc, 'files', 'highscores.json')
        else:
            path = join(direc, 'data', 'highscores.json')
        with open(path, 'r') as f: #catch FileNotFoundError
            old_data = json.load(f)
        for k, h_list in old_data.items():
            settings_list = k.split(',')
            if len(settings_list) == 5:
                settings_list.insert(2, 'False') #distance_to
            (detection, diff, distance_to,
             drag_select, lives, per_cell) = settings_list #unpack
            if detection != '1' or lives != '1' or distance_to != 'False':
                continue #don't include
            if drag_select == 'True':
                drag_select = True
            elif drag_select == 'False':
                drag_select = False
            else:
                drag_select = bool(int(drag_select))
            settings = {'diff':        diff,
                        'drag_select': drag_select,
                        'per_cell':    int(per_cell)}
            hscores_list = get_highscores(settings)
            for h in h_list:
                if not h['name']:
                    continue
                new_h = {k: h[k] for k in HighscoreStruct.elements}
                new_h['time'] = int(1000 * float(h['time'])) #str (s) to int (ms)
                new_h['date'] = int(h['date'])
                new_h['flagging'] = 'F' if h['flagging'] else 'NF'
                new_h['key'] = enchs(settings, new_h) #no check
                if new_h not in hscores_list:
                    hscores_list.append(new_h)
                    added += 1
    elif version >= '2.1': #no highscores in version 2.0
        hfile_paths = glob(join(direc, 'files', '*.csv'))
        if len(hfile_paths) == 0:
            raise FileNotFoundError
        for hfile in hfile_paths:
            settings = splitext(basename(hfile))[0]
            hscores_list = get_highscores(settings)
            add_hscores = [h for h in read_highscores(settings, hfile)
                           if h not in hscores_list]
            hscores_list.extend(add_hscores)
            added += len(add_hscores)
    print(f"Added {added} highscores")
    return added

