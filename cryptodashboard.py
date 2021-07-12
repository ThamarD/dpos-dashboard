# Imports
import requests
import json
import sys
import time
import argparse

from dposconfig import *
from dposfunctions import get_dpos_api_info_v2
from dposfunctions import productivity_check
from dposfunctions import forging_check
from telegram import __send_telegram_message, set_telegram_conf

###########################################################################################
#                                 DPoS Node Dashboard
#                                 Version 0.98
#                                 By Delegate Thamar
###########################################################################################

if sys.version_info[0] < 3:
    print('python2 not supported, please use python3')
    sys.exit()

# Parse command line args
parser = argparse.ArgumentParser(description='Crypto Dashboard')
parser.add_argument('-c', metavar='config.json', dest='cfile', action='store',
                    default='config.json',
                    help='set a config file (default: config.json)')
# parser.add_argument('-y', dest='alwaysyes', action='store_const',
#                     default=False, const=True,
#                     help='automatic yes for log saving (default: no)')

args = parser.parse_args()

# Load the config file
try:
    conf = json.load(open(args.cfile, 'r'))
    set_telegram_conf(conf["telegram_settings"])
except:
    print('Unable to load config file.')
    sys.exit()

if 'logfile' in conf:
    LOGFILE = conf['logfile']
else:
    LOGFILE = 'cdashboard.json'

# Load the blockchain explorer db file
try:
    blockchainexplorerdb = json.load(open("blockchainexplorer.json", 'r'))
except:
    print('Unable to load the blockchain explorer db file: blockchainexplorer.json.')
    sys.exit()


def handle_error(ex, msg, exit):
    error_msg = time.strftime('%Y-%m-%d %H:%M:%S: ') + msg
    if ex is not None:
        error_msg += ': ' + str(ex)
    print(error_msg)
    if exit:
        sys.exit()


def loadLog():
    try:
        data = json.load(open(LOGFILE, 'r'))
    except:
        data = {
            "cryptodashboard_file_version": 0.98,
            "fastsampletime": 0,
            "hourlysampletime": 0,
            "sampleduration": 0,
            "coins": {}
        }
    return data


def savelog(log, filename):
    json.dump(log, open(filename, 'w'), indent=4, separators=(',', ': '))


def get_node_url(url):
    node_url = url
    if not node_url.startswith('http'):
        handle_error(None, 'node_url needs to be in the format http://localhost:<port>', False)
    if node_url.endswith('/'):
        node_url = node_url[:-1]

    return node_url


##############################################################################3
# get_walletbalance
# This function expects an url which is complete and  returns only one number, the balance!
# most API's have two ways to show balance's: a complete website or explicit values of the address.
# You need the API part which shows the explicit values.
#   "explorer": {
#     "bitcoin blockchain": {
#       "exploreraddress": "https://blockchain.info",
#       "api-getbalance": "/q/addressbalance/<address>",
#       "outputvaluesatoshi": "true"
#     },
#     "ether blockchain": {
#       "exploreraddress": "https://api.ethplorer.io",
#       "api-getbalance": "/getAddressInfo/<address>?apiKey=freekey",
#       "1-json-eth": "ETH",
#       "2-json-eth-balance": "balance",
#       "outputvaluesatoshi": "false"
#     }
#   }


def get_walletbalance(url, address):
    walletbalance_exploreraddress = url + address
    # get the base_url of the url which is provided
    from urllib.parse import urlsplit
    base_url = get_node_url("{0.scheme}://{0.netloc}/".format(urlsplit(url)))
    returnfloatdevide = 1

    for explorer in blockchainexplorerdb["explorer"]:
        if blockchainexplorerdb["explorer"][explorer]["exploreraddress"] == base_url:
            walletbalance_exploreraddress = base_url + blockchainexplorerdb["explorer"][explorer][
                "api-getbalance"].replace("<address>", address)
            if blockchainexplorerdb["explorer"][explorer]["outputvaluesatoshi"].lower() == "true":
                returnfloatdevide = 100000000
            break

    try:
        response = requests.get(walletbalance_exploreraddress, timeout=10)
        if response.status_code == 200:
            response_json = response.json()

            # handle the specials: hopefuly not that much!!!
            if base_url == "https://api.ethplorer.io":
                j1 = blockchainexplorerdb["explorer"]["ether blockchain"]["1-json-eth"]
                j2 = blockchainexplorerdb["explorer"]["ether blockchain"]["2-json-eth-balance"]
                response_json_value = response_json[j1][j2]
            elif base_url == "https://explorer.zensystem.io":
                j1 = blockchainexplorerdb["explorer"]["zencash blockchain"]["json-level-1"]
                response_json_value = response_json[j1]
            else:
                response_json_value = response_json

            return float(response_json_value) / returnfloatdevide
        else:
            return float(0)
    except:
        return float(0)


##############################################################################
# get_walletlasttransaction
# This function expects an url which is complete and  returns two numbers, the time and the amount!
# This function expects
def get_walletlasttransaction(url, walletaddress):
    # get the base_url of the url which is provided
    from urllib.parse import urlsplit
    base_url = "{0.scheme}://{0.netloc}/".format(urlsplit(url))

    amountreceived = float(0.0)

    # Get the latest transaction for this Address
    try:
        response = requests.get(base_url + "ext/getaddress/" + walletaddress, timeout=10)
        if response.status_code == 200:
            response_json = response.json()
            last_txs_nr = len(response_json["last_txs"])
            addresses = response_json["last_txs"][last_txs_nr - 1]["addresses"]

            # Get with this address the latest Blockhash for this Address
            response2 = requests.get(base_url + "api/getrawtransaction?txid=" + addresses + "&decrypt=1", timeout=10)
            if response2.status_code != 200:
                return 0, 0
            else:
                response_json2 = response2.json()
                blockhash = response_json2["blockhash"]

                # Get with this address the latest time and amount for the last txid
                response3 = requests.get(base_url + "api/getblock?hash=" + blockhash, timeout=10)
                if response3.status_code == 200:
                    response_json3 = response3.json()
                    timereceived = response_json3.get("time", 0)
                    for payment in response_json2["vout"]:
                        x = payment["scriptPubKey"].get("addresses")
                        if x:
                            for voutaddresses in x:
                                if voutaddresses == walletaddress:
                                    amountreceived = payment["value"]
                    return timereceived, amountreceived
                else:
                    return 0, 0
        else:
            if base_url == "https://chainz.cryptoid.info/":
                # Get the latest transaction for this Address
                # Currently an API key is needed and is not available to receive by email (dd April 9, 2018)
                #            response = requests.get(base_url + "???" + walletaddress)
                #            if response.status_code == 200:
                #                response_json = response.json()
                return 0, 0
            return 0, 0
    except:
        return 0, 0


##############################################################################
# compare dictionary's
# x = dict(a=1, b=2)
# y = dict(a=2, b=2)
# added, removed, modified, same = dict_compare(x, y)
#############################################################################
def dict_compare(d1, d2):
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    intersect_keys = d1_keys.intersection(d2_keys)
    added = d1_keys - d2_keys
    removed = d2_keys - d1_keys
    modified = {o: (d1[o], d2[o]) for o in intersect_keys if d1[o] != d2[o]}
    same = set(o for o in intersect_keys if d1[o] == d2[o])
    return added, removed, modified, same


##############################################################################3
# get_dpos_api_info
# specific for Dpos nodes and their API
# node_url: is the base of the API without the /, which is stripped earlier
# address: can be several identifications: the public address; the publickey
# api_info : indicates which part of the API we use (see the elif statement)

def get_dpos_api_info(node_url, address, api_info):
    if api_info == "publicKey":
        request_url = node_url + '/accounts/getPublicKey?address=' + address
    elif api_info == "delegate":
        request_url = node_url + '/delegates/get?publicKey=' + address
    elif api_info == "accounts":
        request_url = node_url + '/delegates/voters?publicKey=' + address
    elif api_info == "blocks":
        request_url = node_url + '/blocks?generatorPublicKey=' + address
    elif api_info == "balance":
        request_url = node_url + '/accounts/getBalance?address=' + address
    elif api_info == "transactions":
        request_url = node_url + '/transactions?limit=1&recipientId=' + address + '&orderBy=timestamp:desc'
    elif api_info == "epoch":
        request_url = node_url + '/blocks/getEpoch'
    elif api_info == "delegates":
        if address == "":
            request_url = node_url + '/delegates'
        else:
            request_url = node_url + '/accounts/delegates?address=' + address
    else:
        return ""

    try:
        response = requests.get(request_url, timeout=25)
        if response.status_code == 200:
            response_json = response.json()
            if response_json['success']:
                return response_json[api_info]
            else:
                #                    print(request_url + ' ' + str(response.status_code) + ' Failed to get ' + api_info)
                if api_info == "balance":
                    return 0
                return ""
        else:
            print("Error (not 200): " + str(
                response.status_code) + ' URL: ' + request_url + ', response: ' + response.text)
            if api_info == "balance":
                return 0
            return ""
    except:
        print("Error: url is probably not correct: " + request_url)
        # known case: with parameter 'delegates' and if there are no votes returned from API, this exception occurs
        if api_info == "balance":
            return 0
        else:
            return ""


##############################################################################3
# get_dpos_private_vote_info
# specific for Dpos private addresses (if you mark your Delegate Address also a second time as private
# If you vote delegates, you want to keep track if they are still in forging position, besides the % they pay!
# This function checks the known DPoS systems in combination of the private DPoS Wallet address and
# its votes on Delegates load all the forging delegates
#
# function returns 2 values
#   1. the total number of votes a DPoS address in this ecosystem can cast
#   2. a list of names of delegates who are currently not forging (together with the current forging spot)
#
def get_dpos_private_vote_info(coin_nodeurl, address):
    amount_forging_delegates = len(get_dpos_api_info(coin_nodeurl, "", "delegates"))
    private_delegate_vote_info = get_dpos_api_info(coin_nodeurl, address, "delegates")

    # create a dict for the not forging names
    notforgingdelegates = {}

    for networkname in private_delegate_vote_info:
        if "rank" in networkname:
            rate = "rank"
        elif "rate" in networkname:
            rate = "rate"
        else:
            return len(private_delegate_vote_info), notforgingdelegates

        if networkname[rate] > amount_forging_delegates:
            notforgingdelegates[networkname["username"]] = networkname[rate]
    return len(private_delegate_vote_info), notforgingdelegates


def human_format(num, round_to=2):
    magnitude = 0
    if abs(num) < 1000:
        if abs(num) < 100:
            return '{:.{}f}{}'.format(round(num, 1), 1, ['', 'k', 'M', 'G', 'T', 'P'][magnitude])
        else:
            return '{:.{}f}{}'.format(round(num, 0), 0, ['', 'k', 'M', 'G', 'T', 'P'][magnitude])
    else:
        while abs(num) >= 1000:
            magnitude += 1
            num = round(num / 1000.0, round_to)
        return '{:.{}f}{}'.format(round(num, round_to), round_to, ['', 'k', 'M', 'G', 'T', 'P'][magnitude])

def dashboard():
    from urllib.parse import urlsplit
    from datetime import datetime
    import copy

    # read the json, this is the database of the dashbaord
    coininfo_output = loadLog()
    keep4history = 0
    hourlysample = 0

    # get current day in month (we don't need anything else)
    currentDay = datetime.now().day  # datetime's now is localized
    # get the day of the last run of the script from the "fastsampletime"
    if coininfo_output['fastsampletime'] > 0:
        timesampleday = datetime.fromtimestamp(coininfo_output['fastsampletime']).day

        # these are not the same anymore, this run will be the run at around 00:00 (if hourly scheduld) and will be marked
        # as a run to be archived if you want a daily archive with one day history samples
        if timesampleday != currentDay:
            keep4history = 1
    else:
        keep4history = 1

    secondspastsincelastsample = int(time.time()) - coininfo_output['hourlysampletime']
    if secondspastsincelastsample >= (60*60):
        hourlysample = 1
        coininfo_output['hourlysampletime'] = int(time.time())


    # Update last time the cryptodashboard has run
    timestamp = coininfo_output['fastsampletime'] = int(time.time())

    monitoringresults = []

    # loop through all coin names
    for networkname in conf["coins"]:
        coin_type_entry_exists = 0
        amountreceived = 0
        timereceived = 0
        lastforgedblock_timestamp = 0
        view_type = ""

        totalbalance = 0
        delegatename = ""
        rank = 0
        forging = ""            # yes or no
        balance_str = ""        # balance in short-string-notation so: 1.000 = 1k and 1.000.000 = 1M
        producedblocks = 0
        votingweight = 0
        votingweight_str: ""
        missedblocks = 0
        productivity = 0
        nrofvoters = 0
        nrofvotescasted = 0
        notforgingdelegates = ""
        network_explorerlink_with_address = ""

        # loop through the coin specific wallets (entry's)
        coin_type = conf["coins"][networkname]
        for coin_type_entry in coin_type:
            id = coin_type_entry["id"]
            action = coin_type_entry["action"]

            if action == "remove":
                # remove this entry from the cdashboard.json file; not from the config.json file
                try:
                    coininfo_output['coins'].pop(id)
                except:
                    continue
                print("The node entry of -" + id + "- is deleted/removed from the output file (not from the config.json)")
                continue
            elif action == "template":
                # print("This entry is the template entry to show what needs to be filled in, do nothing, next!")
                continue
            elif action == "skip":
                print("The node entry of -" + id + "- is skipped!")
                # todo - do we need to (re)set values to make this item on the outside visible that it is not activly sampled at all anymore, grey-out or so?
                continue

            takesample = 0
            pub_address = coin_type_entry["pubaddress"]
            view_type = coin_type_entry["viewtype"]
            monitoring = coin_type_entry["monitoring"]

            # check if coin_type_entry is in the history; then we need to update
            if id in coininfo_output["coins"]:
                coin_type_entry_exists = 1
            else:
                coin_type_entry_exists = 0

            # when to take a sample
            if monitoring == "yes":     # if coin is monitored => take a sample when crontab is executed, each 10 min?!
                takesample = 1
            elif hourlysample == 1:     # if coin not in monitoring ==> take at least every hour a sample
                takesample = 1

            # Section: dpos_delegate and dpos_private
            if takesample == 1:
                if view_type == "dpos_delegate" or view_type == "dpos_private":
                    network_explorerlink = networksettings[networkname][2]
                    network_explorerlink_with_address = networksettings[networkname][2] + networksettings[networkname][3]
                    network_nodeurl = networksettings[networkname][4]

                    # ARK v2 and higher based nodes/chains
                    if networkname in ark_type_nodes:

                        # get all the delegate info
                        coin_ark_delegateinfo = get_dpos_api_info_v2(networkname, network_nodeurl, pub_address, "delegates")
                        if coin_ark_delegateinfo != "":
                            delegatename = coin_ark_delegateinfo["username"]
                            rank = coin_ark_delegateinfo["rank"]
                            producedblocks = coin_ark_delegateinfo["blocks"]["produced"]
                            votingweight = int(coin_ark_delegateinfo["votes"]) / 100000000

                            try:
                                lastforgedblock_timestamp = coin_ark_delegateinfo["blocks"]["last"]["timestamp"]["unix"]
                            except:
                                lastforgedblock_timestamp = 0

                            # Extract delegate and coin info
                            totalbalance = int(float(get_dpos_api_info_v2(networkname, network_nodeurl, pub_address, "balance"))) / 100000000
                            nrofvoters = int(get_dpos_api_info_v2(networkname, network_nodeurl, pub_address, "voters"))

                            # productivity: calculated over the last 100 rounds.
                            recent_blocks = get_dpos_api_info_v2(networkname, network_nodeurl, pub_address, "blocks2")
                            curr_status = get_dpos_api_info_v2(networkname, network_nodeurl, pub_address, "status")
                            if recent_blocks != "" and curr_status != "":
                                productivity = productivity_check(networkname, recent_blocks, curr_status["now"])
                            else:
                                productivity = 1 # Not sure if this is the right way; When info is not available. I asume there is a problem.

                            network_explorerlink_with_address = network_explorerlink + networksettings[networkname][3] + pub_address
                        else:
                            if monitoring == "yes":
                                thismonitoringmessage = network_nodeurl + " - incorrect or maintenance?"
                                monitoringresults.append({"coin": id, "message": thismonitoringmessage})
                            # skip all coins in for this node type - no use to check other and update with incorrect info
                            break

                    # Lisk 2.0 based nodes/chains
                    elif networkname in lisk_type_nodes:

                        totalbalance = int(float(get_dpos_api_info_v2(networkname, network_nodeurl, pub_address, "balance"))) / 100000000
                        nrofvoters = int(get_dpos_api_info_v2(networkname, network_nodeurl, pub_address, "voters"))

                        # get all the delegate info
                        coin_lisk_delegateinfo = get_dpos_api_info_v2(networkname, network_nodeurl, pub_address, "delegates")
                        if coin_lisk_delegateinfo != "":
                            delegatename = coin_lisk_delegateinfo["username"]
                            coin_pubkey = coin_lisk_delegateinfo["account"]["publicKey"]
                            rank = coin_lisk_delegateinfo["rank"]
                            approval = coin_lisk_delegateinfo["approval"]
                            producedblocks = coin_lisk_delegateinfo["producedBlocks"]
                            votingweight = int(coin_lisk_delegateinfo["vote"]) / 100000000
                            missedblocks = coin_lisk_delegateinfo["missedBlocks"]
                        else:
                            coin_pubkey = ""

                        # get from a dpos address MaxNummerOfVotes you can cast and the names of the delegates who are currently not in the forging state with their forging position!
# not in v3?                                               nrofvotescasted, notforgingdelegates = get_dpos_private_vote_info_lisk(network_nodeurl, pub_address)

                        # get last transaction
                        transactions = get_dpos_api_info_v2(networkname, network_nodeurl, pub_address, "transactions")
                        if len(transactions) > 0:
                            amountreceived = int(transactions["amount"]) / 100000000

                            coin_epoch = get_dpos_api_info_v2(networkname, network_explorerlink, pub_address, "epoch")
                            # epoch "2016-05-24T17:00:00.000Z"
                            # convert the epoch time to a normal Unix time in sec datetime.strptime('1984-06-02T19:05:00.000Z', '%Y-%m-%dT%H:%M:%S.%fZ')
                            if len(coin_epoch) > 0:
                                utc_dt = datetime.strptime(coin_epoch, '%Y-%m-%dT%H:%M:%S.%fZ')
                                # Convert UTC datetime to seconds since the Epoch and add the found transaction timestamp to get the correct Unix date/time in sec.
                                timereceived = (utc_dt - datetime(1970, 1, 1)).total_seconds() + transactions["timestamp"]

                        # get the Date and Time of the last forged block of this delegate
                        blocks_delegateinfo = get_dpos_api_info_v2(networkname, network_nodeurl, coin_pubkey, "blocks")
                        if blocks_delegateinfo:
                            lastforgedblock_timestamp = (utc_dt - datetime(1970, 1, 1)).total_seconds() + blocks_delegateinfo

                        network_explorerlink_with_address = network_explorerlink + "/address/" + pub_address


                    # Lisk 3.0 based nodes/chains
                    elif networkname in liskv3_type_nodes:

                        totalbalance = int(float(get_dpos_api_info_v2(networkname, network_nodeurl, pub_address, "balance"))) / 100000000
                        nrofvoters = int(get_dpos_api_info_v2(networkname, network_nodeurl, pub_address, "voters"))

                        # get all the delegate info
                        coin_lisk_delegateinfo = get_dpos_api_info_v2(networkname, network_nodeurl, pub_address, "account")
                        if coin_lisk_delegateinfo != "":
                            delegatename = coin_lisk_delegateinfo["username"]
                            coin_pubkey = "" # todo coin_lisk_delegateinfo["account"]["publicKey"]
                            rank = coin_lisk_delegateinfo["rank"]
                            producedblocks = 0 # todo coin_lisk_delegateinfo["producedBlocks"]
                            votingweight = int(coin_lisk_delegateinfo["totalVotesReceived"]) / 100000000
                            missedblocks = coin_lisk_delegateinfo["consecutiveMissedBlocks"]
                        else:
                            coin_pubkey = ""

                        # get from a dpos address MaxNummerOfVotes you can cast and the names of the delegates
                        # who are currently not in the forging state with their forging position!
# not in v3?                        nrofvotescasted, notforgingdelegates = get_dpos_private_vote_info_lisk(network_nodeurl, pub_address)

                        # get epoch of chain via explorer API |e.g. epoch "2016-05-24T17:00:00.000Z"
                        # convert epoch time to a normal Unix time in sec
                        coin_epoch = get_dpos_api_info_v2(networkname, network_explorerlink, pub_address, "epoch")
                        utc_dt = 0
                        if len(coin_epoch) > 0:
                            utc_dt = datetime.strptime(coin_epoch, '%Y-%m-%dT%H:%M:%S.%fZ')

                        # get last transaction / and determine the received ammount and time (Convert UTC datetime to seconds)
                        transactions = get_dpos_api_info_v2(networkname, network_nodeurl, pub_address, "transactions")
                        if len(transactions) > 0:
                            amountreceived = int(transactions["amount"]) / 100000000
                            timereceived = (utc_dt - datetime(1970, 1, 1)).total_seconds() + float(transactions["timestamp"])

                        # get the Date and Time of the last forged block of this delegate
                        blocks_delegateinfo = get_dpos_api_info_v2(networkname, network_nodeurl, coin_pubkey, "blocks")
                        if blocks_delegateinfo and len(coin_epoch) > 0:
                            lastforgedblock_timestamp = (utc_dt - datetime(1970, 1, 1)).total_seconds() + blocks_delegateinfo
                        else:
                            lastforgedblock_timestamp = 0

                        network_explorerlink_with_address = network_explorerlink + networksettings[networkname][3] + pub_address

                    # Enkel GNY
                    elif "GNY" in networkname:

                        # get all the delegate info
                        coin_delegateinfo = get_dpos_api_info_v2(networkname, network_nodeurl, pub_address, "delegates")
                        if coin_delegateinfo != "":
                            delegatename = coin_delegateinfo["username"]
                            producedblocks = int(coin_delegateinfo["producedBlocks"])
                            votingweight = int(coin_delegateinfo["votes"]) / 100000000
                            coin_pubkey = coin_delegateinfo["publicKey"]
                            missedblocks = int(coin_delegateinfo["missedBlocks"])
                            nrofvoters = int(get_dpos_api_info_v2(networkname, network_nodeurl, delegatename, "voters"))
                            rank = coin_delegateinfo["rate"]

                            # get the Date and Time of the last forged block of this delegate
                            # lastforgedblock_timestamp = coin_delegateinfo["blocks"]["last"]["timestamp"]["unix"]
                            # lastforgedblock_timestamp = get_dpos_api_info_v2(networkname, network_nodeurl, coin_pubkey, "blocks")

                            # Extract balance
                            totalbalance = int(float(get_dpos_api_info_v2(networkname, network_nodeurl, pub_address, "balance"))) / 100000000


                            # get from a dpos address MaxNummerOfVotes you can cast and the names of the delegates who
                            # are currently not in the forging state with their forging position!
                            nrofvotescasted = 0
                            notforgingdelegates = ""
                            #  todo                nrofvotescasted, notforgingdelegates = get_dpos_private_vote_info_ark(network_nodeurl, pub_address)


                            # # Yield: Productivity calculated over the last 100 rounds.
                            # # Below, isn't working, API can't give last 100 blocks forged by this delegate! But Missedblocks is available
                            # recent_blocks = get_dpos_api_info_v2(networkname, network_nodeurl, delegatename, "blocks2")
                            # curr_status = get_dpos_api_info_v2(networkname, network_nodeurl, delegatename, "status")
                            # if curr_status != "" and recent_blocks != "":
                            #     productivity = int(productivity_check_gny(networkname, recent_blocks, int(curr_status["height"])))
                            # else:
                            #     productivity = 1
                            network_explorerlink_with_address = network_explorerlink + networksettings[networkname][3] + pub_address
                        else:
                            if monitoring == "yes":
                                thismonitoringmessage = network_nodeurl + " - incorrect or maintenance?"
                                monitoringresults.append({"coin": id, "message": thismonitoringmessage})
                            # skip all coins in for this node type - no use to check other and update with incorrect info
                            break

                    elif networkname in otherdpos_type_nodes:
                        # get the public key of this address
                        coin_pubkey = get_dpos_api_info(network_nodeurl, pub_address, "publicKey")
                        if coin_pubkey != "":
                            if coin_pubkey == None:
                                coin_pubkey = ""

                            # first check if url is working, if so, I assume other calls will also work ;-)
                            # there are addresses (wallets) which don't have a pubkey; This address has never-ever sent earlier a transaction through the blockchain!

                            # get the current balance of this address
                            totalbalance = int(float(get_dpos_api_info(network_nodeurl, pub_address, "balance"))) / 100000000

                            # get all the delegate info
                            coin_delegateinfo = get_dpos_api_info(network_nodeurl, coin_pubkey, "delegate")
                            if coin_delegateinfo != "":
                                delegatename = coin_delegateinfo["username"]
                                rank = coin_delegateinfo["rank"]
                                votingweight = int(coin_delegateinfo["vote"]) / 100000000
                                producedblocks = coin_delegateinfo["producedblocks"]
                                missedblocks = coin_delegateinfo["missedblocks"]

                                if networkname == "Adamant":
                                    votingweight = int(coin_delegateinfo["votesWeight"]) / 100000000

                            # get number of voters
                            nrofvoters = len(get_dpos_api_info(network_nodeurl, coin_pubkey, "accounts"))

                            # get from a dpos address MaxNummerOfVotes you can cast and the names of the delegates who are currently not in the forging state with their forging position!
                            nrofvotescasted, notforgingdelegates = get_dpos_private_vote_info(network_nodeurl, pub_address)

                            # get last transaction
                            transactions = get_dpos_api_info(network_nodeurl, pub_address, "transactions")
                            utc_dt = 0
                            if len(transactions) > 0:
                                amountreceived = int(transactions[0]["amount"]) / 100000000

                                coin_epoch = get_dpos_api_info(network_nodeurl, 0, "epoch")
                                # convert the epoch time to a normal Unix time in sec datetime.strptime('1984-06-02T19:05:00.000Z', '%Y-%m-%dT%H:%M:%S.%fZ')
                                if len(coin_epoch) > 0:
                                    utc_dt = datetime.strptime(coin_epoch, '%Y-%m-%dT%H:%M:%S.%fZ')
                                    # Convert UTC datetime to seconds since the Epoch and add the found transaction timestamp to get the correct Unix date/time in sec.
                                    timereceived = (utc_dt - datetime(1970, 1, 1)).total_seconds() + float(transactions[0]["timestamp"])

                            # get the Date and Time of the last forged block of this delegate
                            # todo - check why it isn't working in ADAMANT - call takes about > 20 seconds so it times-out!
                            if networkname != "Adamant":
                                blocks_delegateinfo = get_dpos_api_info(network_nodeurl, coin_pubkey, "blocks")
                                if blocks_delegateinfo:
                                    lastforgedblock_timestamp = (utc_dt - datetime(1970, 1, 1)).total_seconds() + float(blocks_delegateinfo[0]["timestamp"])

                            network_explorerlink_with_address = network_explorerlink + networksettings[networkname][3] + pub_address
                        else:
                            if monitoring == "yes":
                                thismonitoringmessage = network_nodeurl + " - incorrect or maintenance?"
                                monitoringresults.append({"coin": id, "message": thismonitoringmessage})
                            # skip all coins in for this node type - no use to check other and update with incorrect info
                            break
                    else:
                        print("Unknown Network definitions: " + networkname +
                              ", please check your config.json. See dposcoinfig.py for valid -Network definitions-)")
                    # Each 10 minutes - we sample
                    #   Forging status
                    #   Missed blocks status
                    #
                    #
                    # Each Hour - we sample
                    # we need a complete sample, for existing and onboard new coins!
                    #
                    #                    if hourlysample and view_type == "dpos_delegate" and coin_type_entry_exists == 1:
                    # check if networkname/coin already exists? If not, add coin to the output list
                    if coin_type_entry_exists != 1:
                        coininfo_output["coins"][id] = {
                            "coin": networkname,
                            "view_type": view_type,
                            "delegatename": "",
                            "explink": network_explorerlink_with_address,
                            "nrofvotescasted": 0,
                            "nrofnotforingdelegates": 0,
                            "notforgingdelegates": {},
                            "forging": "",
                            "productivity": 0,
                            "missedblocks": 0,
                            "history": []
                        }
                    else:
                        # these items can change now and then by the user...
                        coininfo_output["coins"][id]["explink"] = network_explorerlink_with_address

                    totalbalance_str = human_format(totalbalance, 1)

                    # generic variable coin info
                    coininfo_tocheck = {
                        "timestamp": timestamp,
                        "totalbalance": totalbalance,
                        "totalbalance_str": totalbalance_str,
                        "amountreceived": amountreceived,
                        "timereceived": timereceived,
                        "rank": 0,
                        "votingweight": 0,
                        "votingweight_str": "",
                        "nrofvoters": 0,
                        "producedblocks": 0,
                        "missedblocks": 0,
                        "productivity": 0,
                        "lastforgedblock_timestamp": lastforgedblock_timestamp
                    }

                    # Specific delegate Dpos coin info
                    coininfo_tocheck["rank"] = rank
                    coininfo_tocheck["votingweight"] = votingweight
                    coininfo_tocheck["votingweight_str"] = human_format(votingweight, 1)
                    coininfo_tocheck["nrofvoters"] = nrofvoters
                    coininfo_tocheck["producedblocks"] = producedblocks
                    coininfo_tocheck["missedblocks"] = missedblocks
                    coininfo_tocheck["productivity"] = productivity

                    coininfo_output["coins"][id]["delegatename"] = delegatename
                    coininfo_output["coins"][id].update({"nrofvotescasted": nrofvotescasted})
                    coininfo_output["coins"][id].update({"nrofnotforingdelegates": len(notforgingdelegates)})
                    coininfo_output["coins"][id]["notforgingdelegates"] = notforgingdelegates
                    previousforgingstatus = coininfo_output["coins"][id]["forging"]



                    # try to figure out the change of missedblocks between this sample and the previous
                    # if missedblocksdelta24h > 0 we have an indication, delegate is missing blocks
                    # previous sample:  coininfo_output["coins"][networkname]["missedblocks"]
                    # current sample:   coininfo_tocheck["missedblocks"]
                    # results:
                    #   previous_sample > current_sample  ==> amount missed blocks is still increasing, Not good!
                    #   previous sample <= current sample ==> amount missed blocks is the same or decreasing, Good!
                    # missedblockstatus = color the output cell of this delegate!
                    #       - 2 = Red = increasing
                    #       - 1 = Green = steady or decreasing
                    #       - 0 = transparent = no blocks missing

                    missedblockstatus = 0
                    sample = 0

                    # missedblocks in ARK DPoS do not exist ==> so productivity is used here. # todo make generic for GNY, add Lisk too? Or All?
                    if networkname in ark_type_nodes:
                        missed_previous_sample = int(coininfo_output["coins"][id]["productivity"])
                        missed_current_sample = int(coininfo_tocheck["productivity"])
                        if missed_current_sample < missed_previous_sample:
                            sample = 100 - int(coininfo_tocheck["productivity"])
                            coininfo_output["coins"][id].update({"missedblocks": sample})
                        else:
                            sample = 0
                            coininfo_output["coins"][id].update({"missedblocks": missed_current_sample - missed_previous_sample})
                    else:
                        missed_previous_sample = int(coininfo_output["coins"][id]["missedblocks"])
                        missed_current_sample = int(coininfo_tocheck["missedblocks"])
                        sample = missed_previous_sample - missed_current_sample
                        coininfo_output["coins"][id].update({"missedblocks": sample})

                    try:
                        temp_missedblocksdelta24h = coininfo_output["coins"][id]["missedblocksdelta24h"]
                    except:
                        temp_missedblocksdelta24h = 0

                    # When sample > 0 ==> We are currently missing blocks! When <= 0 ; we are forging again
                    if sample > 0:
                        missedblockstatus = 2
                    else:
                        if temp_missedblocksdelta24h > 0:
                            missedblockstatus = 1
                        else:
                            missedblockstatus = 0

                    # Determine if delegate is in forging position or is missing blocks (yes|no|mis)
                    forging = forging_check(networkname, rank, missedblockstatus)
                    coininfo_output["coins"][id].update({"forging": forging})
                    coininfo_output["coins"][id].update({"missedblockstatus": missedblockstatus})



                    # Monitoring shit TEST todo
                    if monitoring == "yes":
                        thismonitoringmessage = ""
                        if forging != previousforgingstatus:
                            if forging == 'yes':
                                if coin_type_entry_exists == 1:
                                    thismonitoringmessage = "- forging Again!"
                                else:  # first time this entry
                                    thismonitoringmessage = "- added, and forging!"
                            else:
                                if coin_type_entry_exists == 1:
                                    thismonitoringmessage = "- forging STOPPED!"
                                else:  # first time this entry
                                    thismonitoringmessage = "- added, not forging!"
                        if sample > 0:
                            thismonitoringmessage = "- missedblock(s): " + str(abs(sample))

                        monitoringresults.append({"coin": id, "message": thismonitoringmessage})


                    coininfo_alreadypresent = 0
                    modified = {}
                    for coininfohistory in coininfo_output["coins"][id]["history"]:
                        added, removed, modified, same = dict_compare(coininfohistory, coininfo_tocheck)
                        if len(modified) == 1 and "timestamp" in modified:
                            coininfo_alreadypresent = 1
                            break


                    if hourlysample == 1:
                        # archive the coin info:
                        # 1. check if coin info is the same as earlier samples, in the history (timestamp may differ)
                        # 2. for the overview add/overwrite the info to the current coin info.

                        if keep4history == 1:
                            coininfo_alreadypresent = 0

                        if coininfo_alreadypresent == 0:
                            coininfo_output["coins"][id]["history"].append(coininfo_tocheck)

                        # try to figure out the 24h change of balance, rank and nrofvoters
                        coininfo_output["coins"][id]["history"].sort(key=lambda x: x["timestamp"], reverse=True)
                        for coininfohistory in coininfo_output["coins"][id]["history"]:
                            timestamp24hpast = int(time.time()) - 23 * 60 * 59
                            # coin_timestamp_readable = time.strftime("%Y-%m-%d %H:%M", time.localtime(int(coininfohistory["timestamp"])))
                            # timestamp24hpast_readable = time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp24hpast))

                            if coininfohistory["timestamp"] <= timestamp24hpast:
                                rankdelta24h = coininfohistory["rank"] - coininfo_tocheck["rank"]
                                coininfo_output["coins"][id]["rankdelta24h"] = rankdelta24h

                                votersdelta24h = coininfo_tocheck["nrofvoters"] - coininfohistory["nrofvoters"]
                                coininfo_output["coins"][id]["nrofvoters24h"] = votersdelta24h

                                totalbalancedelta24h = coininfo_tocheck["totalbalance"] - coininfohistory["totalbalance"]
                                coininfo_output["coins"][id]["totalbalancedelta24h"] = totalbalancedelta24h

                                try:
                                    votingweightdelta24h = coininfo_tocheck["votingweight"] - coininfohistory["votingweight"]
                                    coininfo_output["coins"][id]["votingweightdelta24h"] = votingweightdelta24h
                                    coininfo_output["coins"][id]["votingweightdelta24h_str"] = human_format(votingweightdelta24h, 1)
                                except:
                                    break

                                try:
                                    producedblocksdelta24h = coininfo_tocheck["producedblocks"] - coininfohistory["producedblocks"]
                                    coininfo_output["coins"][id]["producedblocksdelta24h"] = producedblocksdelta24h

                                    if networkname in ark_type_nodes:
                                        missedblocksdelta24h = 100 - coininfo_tocheck["productivity"]
                                        coininfo_output["coins"][id]["missedblocksdelta24h"] = missedblocksdelta24h
                                    else:
                                        missedblocksdelta24h = coininfo_tocheck["missedblocks"] - coininfohistory["missedblocks"]
                                        coininfo_output["coins"][id]["missedblocksdelta24h"] = missedblocksdelta24h
                                except:
                                    break
                                break

                    if len(modified) > 1 or coininfo_alreadypresent == 0:
                        coininfo_output["coins"][id].update(coininfo_tocheck)

                    print(coininfo_output["coins"][id])
                elif view_type == "masternode" or view_type == "pos_staking" or view_type == "wallet":
                    # Section: masternode, pos_staking and wallet
                    # todo: clean this up if neccesary to split it in masternode, pos_staking and or wallet
                    balance = get_walletbalance(network_explorerlink, pub_address)
                    timereceived, amountreceived = get_walletlasttransaction(network_explorerlink, pub_address)

                    # get the base_url of the url which is provided
                    base_url = "{0.scheme}://{0.netloc}/".format(urlsplit(network_explorerlink))

                    coin_explorerlink = copy.copy(coin_type.get("exploreraddress"))
                    if coin_explorerlink == None:
                        coin_explorerlink = copy.copy(network_nodeurl.replace("wallet", "explorer"))

                    if coin_type_entry_exists != 1:
                        coininfo_output["coins"][networkname] = {
                            "coin": coin_type["coin"],
                            "view_type": coin_type["view_type"],
                            "delegatename": "",
                            "timereceived": timereceived,
                            "explink": base_url + "address/" + pub_address,
                            "history": []
                        }
                    # create temp coininfo block to check if the same values are already in the json, if so, I don't want those values
                    coininfo_tocheck = {
                        "timestamp": timestamp,
                        "rank": "",
                        "totalbalance": balance,
                        "nrofvoters": "",
                        "amountreceived": amountreceived,
                        "timereceived": timereceived
                    }

                    modified = {}
                    coininfo_alreadypresent = 0
                    for coininfohistory in coininfo_output["coins"][networkname]["history"]:
                        added, removed, modified, same = dict_compare(coininfohistory, coininfo_tocheck)
                        if len(modified) == 1 and "timestamp" in modified:
                            coininfo_alreadypresent = 1
                            break

                    if keep4history == 1:
                        coininfo_alreadypresent = 0

                    if coininfo_alreadypresent == 0:
                        coininfo_output["coins"][networkname]["history"].append(coininfo_tocheck)

                    coininfo_output["coins"][networkname]["history"].sort(key=lambda x: x["timestamp"], reverse=True)
                    for coininfohistory in coininfo_output["coins"][networkname]["history"]:
                        timestamp24hpast = int(time.time()) - 23 * 60 * 59
                        coin_timestamp_readable = time.strftime("%Y-%m-%d %H:%M",
                                                                time.localtime(int(coininfohistory["timestamp"])))
                        timestamp24hpast_readable = time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp24hpast))

                        if coininfohistory["timestamp"] <= timestamp24hpast:
                            totalbalancedelta24h = coininfo_tocheck["totalbalance"] - coininfohistory["totalbalance"]
                            coininfo_output["coins"][networkname]["totalbalancedelta24h"] = totalbalancedelta24h
                            break

                    if len(modified) > 1 or coininfo_alreadypresent == 0:
                        coininfo_output["coins"][networkname].update(coininfo_tocheck)

                    print(coininfo_output["coins"][networkname])
                else:
                    print("Unknown cointype: " + coin_type[
                        "cointype"] + ", please check your config.json. Valid cointypes are: dpos_delegate, dpos_private, masternode pos,_staking and wallet.")


    # calculate how long it takes to calculate all the coins
    coininfo_output['sampleduration'] = int(time.time()) - timestamp

    # Create Telegram message
    complete_message = ""
    for result in monitoringresults:
        if len(result["message"]) > 0:
            complete_message += result["coin"] + " " + result["message"] + "\n"
    if complete_message != "":
        __send_telegram_message(complete_message)
    print(complete_message)

    savelog(coininfo_output, LOGFILE)

def logcruncher():
    # read the json, this is the database of the dashbaord
    coininfo_crunched = coininfo_tocrunch = loadLog()

    # Hisotry crunching starts after 48 hour
    daytime = 24 * 60 * 60
    currenttime = int(time.time())

    today_timestamp_readable = time.strftime("%Y-%m-%d", time.localtime(int(currenttime)))
    yesterday_timestamp_readable = time.strftime("%Y-%m-%d", time.localtime(int(currenttime) - daytime))

    # for every coin, crunch the history
    for networkname in coininfo_tocrunch["coins"]:

        pasttime = currenttime
        coininfohistory = sorted(coininfo_tocrunch["coins"][networkname]["history"],
                                 key=lambda k: ("timestamp" not in k, k.get("timestamp", None)), reverse=True)
        coin_daytimestamparray_readable = []
        coinhisroytitem_temp = {
            "history": []
        }

        for coinhisroytitem in coininfohistory:
            # When history < 2 days (48 hours):  every hour needs 1 entry
            # after this 1 day is 1 entry in the log

            coin_timestamp_readable = time.strftime("%Y-%m-%d", time.localtime(int(coinhisroytitem["timestamp"])))

            # If coin_timestamp is from today; add them all
            if coin_timestamp_readable == today_timestamp_readable or coin_timestamp_readable == yesterday_timestamp_readable:
                coinhisroytitem_temp["history"].append(coinhisroytitem)


            # If coin timestamp is not from today or yesterday; add only the first of a certain date and skip the rest of dat date
            elif pasttime - 2 * daytime >= coinhisroytitem["timestamp"]:
                if coin_timestamp_readable not in coin_daytimestamparray_readable:
                    coinhisroytitem_temp["history"].append(coinhisroytitem)

                    # add this timestamp to the compare array -  we don't need another sample for this date!
                    coin_daytimestamparray_readable.append(
                        time.strftime("%Y-%m-%d", time.localtime(int(coinhisroytitem["timestamp"]))))

        coininfo_crunched["coins"][networkname]["history"] = coinhisroytitem_temp["history"].copy()
        savelog(coininfo_crunched, LOGFILE)


#########################################################
# todo
# in HTML show a Log environment
# make a dark/light mode in the Bootstrap HTML
# create a toggle in de HTML for each node to switch on/off the monitoring
# missedblocks in ARK DPoS do not exist ==> so productivity is used here. Make generic for GNY, add Lisk too? Or All?


if __name__ == "__main__":
    dashboard()
    if conf["crunch_history"]:
        logcruncher()
