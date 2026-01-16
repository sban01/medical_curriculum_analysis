# Learning objectives BME recognition via MetaMap
# This script relies on the database layout and tables being filled via scipt extract_actionverbs.py first.
# It also relies on the NIH metamap server, and having a registered UMLS account with API keys.
# The metamap server on the UMLS website has been discontiued since 2025. To run this script, you have to install a metamap server and call it in the script below.
#
# Stephan Bandelow, Janaury 2024

import sqlite3
import utils
import Concept
    
# database connection
dbcon = sqlite3.connect('semantics.db', detect_types=sqlite3.PARSE_DECLTYPES)


#################### get tokens via MetaMap ########################
import requests
from skr_web_api import Submission
from Concept import Corpus  # Concept class from pymetamap MMI parser

# MetaMap Web API init
email = 'none'
apikey = 'none'
inst = Submission(email, apikey)
mmargs = "-y -N -R MSH,UWDA,SNOMEDCT_US,MTH,ICD10CM" # y = word sense disambiguation, N = MMI output, R = restrict lexicon: include MESH (MSH), UWDA (Digital Anatomist) and SNOMED CT US edition (SNOMEDCT_US), UMLS Metathesaurus (MTH), International Classification of Diseases, 10th Edition, Clinical Modification, 2022 (ICD10CM)
fltPOS = {'noun', 'adj'} # filter POS for nouns and adjectives only

cuis = [] # list of unique UMLS CUI codes (concept IDs)
ucons = [] # final unique concept (tuple: DB id, CUI, semtypes, name, MeSH code, token) list for upload to table concepts
objmap = [] # map between objectives and concepts for upload to table objMap
objectives = utils.db_readSQL(dbcon, 'SELECT * FROM objectives') # objectives list with id codes for foreign key

for objtv in objectives:
    print ('Processing objective ' + str(objtv[0]) + ' out of ' + str(len(objectives)) + ' total.')
    sents = utils.splitSentences (objtv[7]) # replace according to replace dictionary and split into sentences
    sentidx = 0 # iterate by numeric index so we can repeat in case of bad request return status
    while sentidx < len(sents):
        inst.init_mm_interactive(sents[sentidx], args = mmargs)
        response = inst.submit()
        if (response.status_code != 200):
            # no valid response, run request loop again without increasing idx
            continue
        else:
            sentidx += 1
        concepts = Corpus.fromText(response.text) #process MMI fielded list of matches
        for concept in concepts:
            if type(concept) == Concept.ConceptAA:
                # metamap returned AA (abbreviations & acronyms info, need to submit expanded token to get standard MMI
                # check first if sentence also contained expanded token, then no need to process further
                if concept.long_form.lower() in sents[sentidx].lower():
                    # sentence already contains expanded token, just drop abbreviation to avoid repeat
                    continue
                else:
                    # look up expanded abbreviation and pass result to subsequent concept MMI eval
                    inst.init_mm_interactive(concept.long_form, args = mmargs)
                    response = inst.submit()
                    concept = Corpus.fromText(response.text)[0] #process MMI fielded list of matches
            if concept.pos in fltPOS: # only retain concepts matching POS filter list
                if concept.cui in cuis:
                    # duplicate CUI, find existing concept record and link to objective
                    concid = cuis.index(concept.cui) + 1 #get concept ID
                    # save objid, sentence number, tokenid, Metamap score and trigger info (from MM) to table objMap
                else:
                    # new unique CUI, add to concept list and link to objective
                    cuis.append(concept.cui)
                    concid = len(cuis) #auto-increment concept ID
                    # store concept id, cui, prefName, semtypes, meshcode, token in table concepts
                    ucons.append((concid, concept.cui, concept.preferred_name, concept.semtypes, concept.tree_codes, concept.preferred_name))
                # save objid, sentence number, tokenid, Metamap score and trigger info (from MM) to table objMap
                objmap.append((objtv[0], sentidx, concid, concept.score, concept.trigger))

# upload objectives map and concepts table to DB
sql = 'INSERT INTO concepts (id, cui, prefName, semtypes, meshcode, token) VALUES (?, ?, ?, ?, ?, ?)'
dbcon.executemany(sql, ucons)
dbcon.commit()
sql = 'INSERT INTO objMap (objid, sentence, conceptid, mmscore, trigger) VALUES (?, ?, ?, ?, ?)'
dbcon.executemany(sql, objmap)
dbcon.commit()

# add count of concept occurences in different objectives to objMap (to find unique and common concepts later)
concRepeats = utils.db_readSQL(dbcon, 'SELECT COUNT(conceptid), conceptid FROM objMap GROUP BY conceptid')
sql = 'UPDATE concepts SET repeats = ? WHERE id = ?'   
dbcon.executemany(sql, concRepeats)
dbcon.commit()

dbcon.close()
