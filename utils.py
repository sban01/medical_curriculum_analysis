# data handling utilities for BME processing, token list handling and DB format conversions
# Stephan Bandelow, Janaury 2024

import sqlite3
import numpy as np
import io   # for array <-> byte conversions
from sentence_splitter import split_text_into_sentences
#from nltk.tokenize import sent_tokenize #split into sentences. Doesn't deal well with abbreviations (e.g., i.e., etc), sentence splitter above works better.

# database schema
def createTables (conn):
    sql = 'CREATE TABLE IF NOT EXISTS objectives (id INTEGER PRIMARY KEY, course TEXT NOT NULL, module TEXT NOT NULL, discipline TEXT NOT NULL, lecture TEXT, title TEXT, code TEXT UNIQUE NOT NULL, objective TEXT NOT NULL, longvec ARRAY, shortvec ARRAY)' #longvec is sum of underlying concept vectors, shortvec is DR-compressed version
    conn.execute(sql)
    sql = 'CREATE TABLE IF NOT EXISTS objMap (id INTEGER PRIMARY KEY, objid INTEGER NOT NULL, sentence INTEGER DEFAULT 0, conceptid INTEGER NOT NULL, mmscore REAL, trigger TEXT)'
    conn.execute(sql)
    sql = 'CREATE TABLE IF NOT EXISTS concepts (id INTEGER PRIMARY KEY, cui TEXT, prefName TEXT, semtypes TEXT, meshcode TEXT, token TEXT NOT NULL, repeats INTEGER, longvec ARRAY, shortvec ARRAY)' #longvec from BioWordVec model (200 pos), shortvec are DR-compressed versions
    conn.execute(sql)
    sql = 'CREATE TABLE IF NOT EXISTS replaceMap (id INTEGER PRIMARY KEY, token TEXT UNIQUE NOT NULL, replace TEXT)'
    conn.execute(sql)
    sql = 'CREATE TABLE IF NOT EXISTS actionVerbs (id INTEGER PRIMARY KEY, token TEXT UNIQUE NOT NULL)'
    conn.execute(sql)
    sql = 'CREATE TABLE IF NOT EXISTS AVmap (objid INTEGER, sentence INTEGER, AVid INTEGER, verb TEXT, bloom REAL, PRIMARY KEY (objid, sentence))'
    conn.commit()

# wrapper for sentence tokenizer to allow easy swapping out of underlying function
# arguments: multi-sentence text
# return: array of sentence(s)
def splitSentences (text):
    #sents = sent_tokenize(text) #NLTK method, doesn't work well with abbreviations and other details
    sents = split_text_into_sentences(text = text, language='en') #works well for most objectives
    return sents

# helper dictionaries for pre-processing
actverb_mods = {"using", "given", "based_on", "from"}  #action verb modifiers, where it appears after first comma

# return action verb from sentence
# TODO: include potential additional action verbs per sentence (e.g. 'describe and analyse...' or 'list, describe and analyse...')
def get_actverb (sentence, dict_AV, dict_RPL):
    sentence = sentence.lower()
    sentence = replace_all(sentence, dict_RPL)
    words = sentence.split(" ")             # split around whitespace
    if "" in words: words.remove("")        # remove empty items
    actverb = words[0].lower().strip(', ')  # strip whitespace, commas
    if actverb in actverb_mods:
        # action verb position modifier at start, action verb after 1st comma
        actverb = ""
        sections = sentence.split(", ")
        if (len(sections) > 1):
            actverb = sections[1].split(" ")[0]
    if actverb in dict_AV:
        # action verb found in approved list
        return actverb
    else:
        # no action verb in position 1, check for whitelisted action verb until end of sentence
        # TODO: possibly only look until next comma, but current method already works, not needed for now
        for word in words:
            if word in dict_AV:
                actverb = word.strip(', ')
                return actverb
    return ''

# returns results from query 'sql' as 2D data matrix (list of tuples, row = tuple)
def db_readSQL(conn, sql):
    res = conn.execute (sql)
    res = res.fetchall()
    return [list(row) for row in res]   # returns as list of lists

# save 2D matrix (list of tuples) or 1D list as single column to DB table
def db_writeSQL(conn, sql, data):
    if (type(data[0]) == str):
        # convert 1D list of strings into list of tuples to use as single column in executemany
        data = zip(iter(data))
    conn.executemany(sql, data)
    conn.commit()

# read file with 1 token/row, return tokens as array
def read_tokenlist(filename):
    tokens = []
    f = open(filename, 'r')
    row = f.readline()
    while row:
        tokens.append(row.lower().replace('\n', ''))    # make everything lowercase and strip \n newlines
        row = f.readline()
    f.close()
    return(tokens)

# write token array to file as 1 token/row
def write_tokenlist(tokens, filename):
    f = open(filename, 'w')
    for token in tokens:
        f.write (token)
        f.write ('\n')
    f.close()

# save DB table as csv & expand arrays to list of numbers (for analysis in R)
# requires numpy array adpaters and SQLite row factory init after DB connection init (dbcon.row_factory = sqlite3.Row)
def db_query2csv (conn, sql, filename, codepage = 'cp1252'):
    coldefs = [] #column info: name, type, array length (if np.ndarray)
    res = conn.execute(sql)
    rows = res.fetchall()
    colnames = rows[0].keys()
    headernames = []
    #find numpy array columns and adjust colnames in header
    for idx, col in enumerate(rows[0]):
        coltype = type(col)
        colname = colnames[idx]
        if coltype == np.ndarray:
            #numpy array: expand to comma-separated string
            coldefs.append((colname, coltype, len(col)))
            for i in range(1, len(col) + 1):
                headernames.append(colname + str(i))
        else:
            #other column type: no modifications
            coldefs.append((colname, coltype, 1))
            headernames.append(colname)
    with open(filename, 'w', encoding = 'utf-8') as f:
        f.write(', '.join(headernames) + '\n')
        fields = []
        for row in rows:
            fields = []
            for idx, field in enumerate(row):
                if coldefs[idx][1] == np.ndarray:
                    #expand values to comma-sep list (NULL values if source val is NULL)
                    if hasattr(field, "__len__"):
                        #append all element of numpy array as list
                        fields.extend(str(e) for e in list(field))
                    else:
                        #single NULL value returned, make list of NAs for R
                        fields.extend(['NA'] * coldefs[idx][2])
                else:
                    if field is None:
                        fields.append('NA')
                    else:
                        fields.append("'" + str(field) + "'")
            f.write(', '.join(fields) + '\n')

# array to byte sequence for DB storage - could add compressor if many rows
def adapt_array(arr):
    out = io.BytesIO()
    np.save(out, arr)
    out.seek(0)
    return sqlite3.Binary(out.read())

# byte sequence to array to load as np.array
def convert_array(text):
    out = io.BytesIO(text)
    out.seek(0)
    return np.load(out)

# replace all dictionary dict terms in text
def replace_all(text, dict):
    for i, j in dict.items():
        text = text.replace(i, j)
    return text
