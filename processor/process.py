'''
COMP90024
Team 11
Marco Marasco - 834882
Austen McClernon - 834063
Sam Mei - 1105817
Cameron Wong - 1117840
'''

import couchdb
from collections import defaultdict
import traceback
import datetime
import os
import config
import time
import sys
import requests
from requests.auth import HTTPBasicAuth

def saveDB(database, data):
    '''
    Save a list of documents to a database.
    '''

    server = couchdb.Server("http://%s:%s@127.0.0.1:5984/" % (config.COUCHDB_USER, config.COUCHDB_PASSWORD))

    try:
        db = server[database]
    except:
        try:
            server.create(database)
        except:
            pass
        db = server[database]

    for i in data:
        try:
            if not db.get(i):
                db.save(data[i])
            else:
                doc = db[i]
                for j in data[i]:
                    doc[j] = data[i][j]
                db.save(doc)

        except:
            pass


def addSent(data, dict_key, sentiment, value):

    if not data.get(dict_key):
        data[dict_key] = {}
        data[dict_key]['sentiments'] = defaultdict(int)

    data[dict_key]['sentiments'][sentiment] += value

def updateDB(database, command):

    count = 0

    # Request data from database
    data = requests.get(command, auth = HTTPBasicAuth(config.COUCHDB_USER, config.COUCHDB_PASSWORD))
    data = data.json()['rows']

    # Results dictionary
    full_data = defaultdict(dict)
    melbourne = False

    # Save full city data too
    if database == 'users':
        melbourne = True
        melbourne_data = defaultdict(dict)

    for i in data:
        try:

            _id = i['key'][0]
            if not full_data.get(_id):
                full_data[_id] = {'_id': _id}
                for d in config.dates:
                    full_data[_id][d] = {}
                    full_data[_id][d]['sentiments'] = {str(i):0 for i in range(1,11)}


            # Date details
            year = i['key'][1]
            month = i['key'][2]
            sentiment = str(i['key'][-1])
            dict_key = str(year) + '-' + str(month)

            addSent(full_data[_id], dict_key, sentiment, i['value'])

            if melbourne:
                addSent(melbourne_data, dict_key, sentiment, i['value'])

        except Exception as e:
            traceback.print_exc()
            pass

    # Compute average and count for weeks
    for i,j in full_data.items():
        for week in j:
            try:
                sents = j[week]['sentiments']
                j[week]['count'] = sum(sents.values())
                j[week]['average'] = sum([int(x)*y for x,y in sents.items()]) / sum(sents.values())
            except:
                pass
    
    # Save data
    saveDB(database, full_data)
    
    
    if melbourne:
        for i,j in melbourne_data.items():
            try:
                melbourne_data[i]['_id'] = i
                sents = j['sentiments']
                j['count'] = sum(sents.values())
                j['average'] = sum([int(x)*y for x,y in sents.items()]) / sum(sents.values())
            except:
                pass

        saveDB('melbourne', melbourne_data)



def main():

    while True:
        try:
            updateDB('website_suburb', config.SUBURB_GET)
        except Exception as e:
            print(e)
            pass
        try:
            updateDB('users', config.USER_GET)
        except Exception as e:
            print(e)
            pass
        time.sleep(3600 * 6)

