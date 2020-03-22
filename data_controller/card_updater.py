import json
import requests
import time
import copy
from pymongo import MongoClient

MAX_UPDATE_SIZE = 15
API = 'https://bandori.party/api/'

# This is ugly until I find time for a better solution...
def update_task():
    while True:
        print('Getting cards...')
        client = None
        try:
            client = MongoClient('localhost', 27017)
            db = client['haha-no-4star']

             # Get card ids from database and api.
            db_card_ids = set(get_card_ids(db))
            db_member_ids = set(get_member_ids(db))

            api_card_ids = set(json.loads(
                    requests.get(API + 'cardids').text)) 
            api_member_ids = set(json.loads(
                    requests.get(API + 'memberids').text)) 

            new_card_ids = list(api_card_ids - db_card_ids)
            new_member_ids = list(api_member_ids - db_member_ids)

            if len(new_member_ids) > 0:
                new_member_ids = new_member_ids[:MAX_UPDATE_SIZE]
                print('Getting members ' + str(new_member_ids))
                for i in new_member_ids:
                    req = requests.get(url=API + 'members/' + str(i))    
                    res = json.loads(req.text)
                    upsert_member(db, res)

            if len(new_card_ids) > 0:
                new_card_ids = new_card_ids[:MAX_UPDATE_SIZE]
                print('Getting cards ' + str(new_card_ids))
                for i in new_card_ids:
                    req = requests.get(API + 'cards/' + str(i))                
                    res = json.loads(req.text)
                    if validate_card(res):
                        upsert_card(db, res)


     
        except Exception as e:
            print(e)

        finally:
            client.close()
            time.sleep(60)


def get_card_ids(db) -> list:
    """
    Gets a list of all card IDs in the datase.

    :return: List of card IDs.
    """
    return db['cards'].distinct('_id')


def get_member_ids(db) -> list:
    return db['members'].distinct('_id')

def get_members(db, ids: list) -> dict:
        """
        Gets a list of members from the database.

        :param ids: List of members IDs to get.

        :return: Matching cards.
        """
        search = {'_id': {'$in': ids}}
        return db['members'].find(search)

def upsert_member(db, member: dict):
    """
    Inserts a meber into the member collection if it does not exist.

    :param card: Member dictionary to insert.
    """
    member = copy.deepcopy(member)
    member['_id'] = member['id']
    del member['id']

    doc = {'_id': member['_id']}
    setMember = {'$set': member}

    db['members'].update(doc, setMember, upsert=True)

def upsert_card(db, card: dict):
    """
    Inserts a card into the card collection if it does not exist.

    :param card: Card dictionary to insert.
    """
    card = copy.deepcopy(card)
    card['_id'] = card['id']
    del card['id']

    # Replace member id with member info.
    members = get_members(db, [card['member']])
    if not members:
        return

    member = members[0]
    member['id'] = member['_id']
    del member['_id']
    card['member'] = member

    doc = {'_id': card['_id']}
    setCard = {'$set': card}

    db['cards'].update(doc, setCard, upsert=True)


def validate_card(card: dict) -> bool:
    if not card['name']:
        return False
    if not card['image'] and not card['image_trained']:
        return False
    if not card['art'] and not card['art_trained']:
        return False
    return True
