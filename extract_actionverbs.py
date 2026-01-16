# Extract action verbs and thei Bloom level ratings for a list of learning objectives.
# The objectives should be in full sentence format, parsing relies on syntactic structure.
# An example learning objectives file is included. This script relies on this column layout:
# id, course, module, discipline, lecture code, lecture title, objective code, objective text
# If you use a different column layout, please adjust the script below (row 98, 99, 115 and the database schema).
#
# Stephan Bandelow, January 2024

objectives_file = 'objectives.csv'  # learning objectives file (in csv fomat)

import csv
import sqlite3
import numpy as np
from itertools import chain
import utils    # local utility functions

    
# database connection
dbcon = sqlite3.connect('curriculum.db', detect_types=sqlite3.PARSE_DECLTYPES)
utils.createTables (dbcon)    # create all necessary database tables if they don't exist already

# helper dictionaries
table_AV = utils.db_readSQL(dbcon, 'SELECT id, verb FROM actionVerbs') # action verbs from database table
dict_AV = dict((row[1], idx) for idx, row in enumerate(table_AV))  # dict with database IDs, keyed by action verbs (for fast verb lookup)
dict_RPL = dict(utils.db_readSQL(dbcon, 'SELECT token, replace FROM replaceMap')) # token replacement dictionary from table replaceMap
dict_PREP = {"\n": "", "\"": "", "\'": "", "  ": " ", "\t": " ", "\u200b": "", "\u2011": "", "\u2010": "", "\u202f": "", "\u0394": ""} #remap dictionary for pre-processing all fields (strip newlines, remove quotes, double to single space, tab to space, strip unknown unicode chars)


############## process objectives input file (csv) ##################
header = []
with open(objectives_file, encoding = 'utf-8') as csvfile:
    objreader = csv.reader(csvfile, delimiter = ',', dialect = 'excel')
    header = next(objreader)
    objidx = header.index('objective')
    rows = [] #container for list of lists that cointains fields by rows (2D insert data matrix for executemany)
    for row in objreader:
        for i in range(len(row)):
            row[i] = utils.replace_all(row[i], dict_PREP) #pre-processing (cleanup) of all fields
        row[objidx] = row[objidx].strip() #remove leading and trailing whitespace from objective text
        rows.append(row) 
header[0] = 'course' #clean up up 1st column name

#check that we have unique objective codes and separate duplicates
uniqueCodes = []
dupCodes = []
objectives = []
for row in rows:
    if row[5] not in uniqueCodes:
        uniqueCodes.append(row[5])
        objectives.append(row)
    else:
        dupCodes.append(row)
print ('Found ' + str(len(rows)) + ' objectives, ' + str(len(objectives)) + ' unique, ' + str(len(dupCodes)) + ' duplicates.')
del(rows)

# save duplicates to csv file for feedback to faculty
with open('duplicateObjectives.csv', 'w', encoding='UTF8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(dupCodes)
del(dupCodes)

# insert objectives list into objectives table
varnames = "', '".join(header)
sql = "INSERT INTO objectives ('" + varnames + "') VALUES (?, ?, ?, ?, ?, ?, ?)"
dbcon.executemany(sql, objectives)
dbcon.commit()

# get fresh objectives list with ID from DB
objectives = utils.db_readSQL(dbcon, 'SELECT * FROM objectives') #get fresh objectives list with id codes for foreign key

# get action verbs
AVlist = []
foundAV = noAV = 0
for row in objectives:
    sentences = utils.splitSentences (row[7]) #replace according to replace dictionary and split into sentences
    for sentnum, sentence in enumerate(sentences):
        av = utils.get_actverb(sentence, dict_AV, dict_RPL)
        if(av == ''):
            AVlist.append([row[0], sentnum, None, '', None]) #store objid, sentence #, action verb ID, action verb, numeric bloom level
            noAV = noAV + 1
        else:
            AVlist.append(list(chain([row[0], sentnum], table_AV[dict_AV[av]]))) #store objid, sentence #, action verb ID, action verb, numeric bloom level
            foundAV = foundAV + 1
print (str(foundAV) + '/' + str(foundAV + noAV) + ' action verbs identified.') # 12378/13224 action verbs identified.

# AV map table with id - link to objective ID, sentence #, action verb id in table actionVerbs, verb & BLoom level
sql = "INSERT INTO AVmap VALUES (?, ?, ?, ?, ?)"
dbcon.executemany(sql, AVlist)
dbcon.commit()

dbcon.close()
