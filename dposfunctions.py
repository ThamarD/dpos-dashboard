import requests

from dposconfig import *

__author__ = 'dutch_pool'

# #############################################################################
# get_dpos_api_info
# specific for Dpos nodes and their API - Blockchain specific
#
# blockchain:   which blochain is this
# node_url:     is the base of the API without the /, which is stripped earlier
# address:      can be several identifications: the public address; the publickey
# api_info :    indicates which part of the API we use (see the elif statement)
#
# https://api.ark.io/api/delegates/AbxUBkEmEGb3kahQUKJ6LfqsKWGcy3nTij/voters?page=1&limit=1
#
#

def get_dpos_api_info_v2(blockchain, node_url, address, api_info):
    if blockchain in ark_type_nodes:
        return get_dpos_api_info_ark(node_url, address, api_info)
    elif blockchain in lisk_type_nodes:
        return get_dpos_api_info_liskv2(node_url, address, api_info)
    elif "GNY" in blockchain:
        return get_dpos_api_info_gny(node_url, address, api_info)
    #todo  elif blockchain == "olddpos":
    #     return get_dpos_api_info_OldDPoS(node_url, address, api_info)
    else:
        return ""


# #############################################################################
# get_dpos_api_info
# specific for Dpos nodes and their API - Blockchain specific
#
# blockchain:   which blochain is this
# node_url:     is the base of the API without the /, which is stripped earlier
# address:      can be several identifications: the public address; the publickey
# api_info :    indicates which part of the API we use (see the elif statement)
#
# https://api.ark.io/api/delegates/AbxUBkEmEGb3kahQUKJ6LfqsKWGcy3nTij/voters?page=1&limit=1
#

def get_dpos_api_info_ark(node_url, address, api_info):
        if api_info == "publicKey":
            request_url = node_url + '/wallets/' + address
        elif api_info == "delegate":
            request_url = node_url + '/delegates/' + address
        elif api_info == "accounts":
            request_url = node_url + '/delegates/voters?publicKey=' + address
        elif api_info == "blocks":
            request_url = node_url + '/delegates/' + address + '/blocks?page=5&limit=2'
        elif api_info == "blocks2":
            request_url = node_url + '/delegates/' + address + '/blocks'
        elif api_info == "balance":
            request_url = node_url + '/wallets/' + address
        elif api_info == "transactions":
            request_url = node_url + '/transactions?limit=1&recipientId=' + address + '&orderBy=timestamp:desc'
        elif api_info == "voters":
            request_url = node_url + '/delegates/' + address + "/voters?page=1&limit=1"
        elif api_info == "epoch":
            request_url = node_url + '/blocks/getEpoch'
        elif api_info == "status":
            request_url = node_url + '/node/status'
        elif api_info == "delegates":
            if address == "":
                request_url = node_url + '/delegates'
            else:
                request_url = node_url + '/delegates/' + address
        else:
            return ""

        try:
            response = requests.get(request_url, timeout=12)
            if response.status_code == 200:
                response_json = response.json()
                if response_json['data']:
                    if api_info == "delegates" or api_info == "status":
                        return response_json["data"]
                    # if an address is not initialised; the publicKey can be empty = None
                    elif api_info == "publicKey":
                        if response_json["data"][api_info] == None:
                            return ""
                        else:
                            return response_json["data"][api_info]
                    elif api_info == "voters":
                        return response_json["meta"]["totalCount"]
                    elif api_info == "blocks":
                        return response_json["data"][0]["timestamp"]["unix"]
                    elif api_info == "blocks2":
                        return response_json
                    else:
                        return response_json["data"][api_info]
                else:
                    #print(request_url + ' ' + str(response.status_code) + ' Failed to get ' + api_info)
                    if api_info == "balance":
                        return 0
                    return ""
            else:
                print("Error (not 200): " + str(
                    response.status_code) + ' URL: ' + request_url + ', response: ' + response.text)
                if api_info == "balance" or api_info == "voters":
                    return 0
                return ""
        except:
            print("Error: url is probably not correct: " + request_url)
            # known case: with parameter 'delegates' and if there are no votes returned from API, this exception occurs
            if api_info == "balance" or api_info == "voters":
                return 0
            else:
                return ""



# #############################################################################
# calc_round
#

def calc_round(height, blockchain):

    nrofvalidators = networksettings[blockchain][0]
    data = divmod(height, nrofvalidators)
    if data[1] == 0:
        result = data[0]
    else:
        result = data[0] + 1
    return result


# #############################################################################
# productivity_check
# blockchain = which chain
# recent_blocks =  last 100 blocks from the block chain
# curr_height = current height of the block chain

def productivity_check(blockchain, recent_blocks, curr_height):

    # Check how much rounds are available with this call - I expect 100 in a continious situation. If less than 2; stop!
    total_rounds = recent_blocks['meta']['count']

    if total_rounds < 2:
        return

    missed = 0
    forged = 0

    net_round = calc_round(curr_height, blockchain)
    cur_round = calc_round(recent_blocks['data'][0]['height'], blockchain)

    if net_round > cur_round + 1:
        missed += net_round - cur_round - 1
    else:
        forged += 1

    # check 100 blocks, which this delegate has forged; if delegate missed a block; the normalised blocknr is disturbed;
    for i in range(0, total_rounds - 1):
        cur_round = calc_round(recent_blocks['data'][i]['height'], blockchain)
        prev_round = calc_round(recent_blocks['data'][i + 1]['height'], blockchain)
        if prev_round < cur_round - 1:
            if cur_round - prev_round - 1 > total_rounds - missed - forged:
                missed += total_rounds - missed - forged
                break
            else:
                missed += cur_round - prev_round - 1
        else:
            forged += 1
    productivity = (forged * 100)/(forged + missed)
    return round(productivity)

# #############################################################################
# forging_check
# blockchain = which chain
# rank = curent rank of this delegate
# missedblockstatus = 2 ==> currently missing blocks, others are 0, not missing blocks; 1 formerly missed blocks

def forging_check(blockchain, rank, missedblockstatus):

    if rank <= networksettings[blockchain][0]:
        if missedblockstatus == 2:
            return "mis"
        else:
            return "yes"
    else:
        return "no"


# #############################################################################
# get_dpos_api_info
# specific for Dpos nodes and their API
# node_url: is the base of the API without the /, which is stripped earlier
# address: can be several identifications: the public address; the publickey
# api_info : indicates which part of the API we use (see the elif statement)
#
# a bit adhoc, but it should work https://node08.lisk.io/api/blocks

# https://wallet.mylisk.com/api/transactions?recipientId=139289198949001083L&toTimestamp=1540633350&limit=10&offset=0&sort=amount%3Adesc
# https://explorer.mylisk.com/api/getBlockStatus
# https://node01.lisk.io/api/transactions?senderIdOrRecipientId=139289198949001083L&limit=10&offset=0&sort=timestamp:desc

# /api/blocks?limit=10&offset=0&generatorPublicKey=ec111c8ad482445cfe83d811a7edd1f1d2765079c99d7d958cca1354740b7614&sort=timestamp%3Aasc

def get_dpos_api_info_liskv2(node_url, address, api_info):

    if api_info == "balance" or api_info == "publicKey":
        request_url = node_url + '/api/accounts?address=' + address
    elif api_info == "delegates":
        request_url = node_url + '/api/delegates?address=' + address
    elif api_info == "forgingdelegates":
        request_url = node_url + '/api/delegates?offset=0&limit=101&sort=rank%3Aasc'
    elif api_info == "transactions":
        request_url = node_url + '/api/transactions?recipientId=' + address + '&limit=10&offset=0&sort=timestamp:desc'
    elif api_info == "epoch":
        request_url = node_url + '/api/getBlockStatus'
    elif api_info == "blocks":
        request_url = node_url + '/api/blocks?limit=10&offset=0&generatorPublicKey=' + address + '&sort=timestamp:desc'
    elif api_info == "voters":
        request_url = node_url + '/api/voters?address=' + address
    elif api_info == "votes":
        request_url = node_url + '/api/votes?address=' + address + '&offset=0&limit=101&sort=username%3Aasc'
    else:
        return ""

    try:
        response = requests.get(request_url, timeout=10)
        if response.status_code == 200:
            response_json = response.json()

            if api_info == "epoch":
                return response_json[api_info]
            elif response_json["data"]:
                if api_info == "publicKey":
                    return response_json["data"][0]["publicKey"]
                if api_info == "balance":
                    return response_json["data"][0][api_info]
                elif api_info == "voters":
                    return int(response_json["data"]["votes"])
                elif api_info == "votes":
                    return response_json["data"]["votes"]
                elif api_info == "blocks":
                    return response_json["data"][0]["timestamp"]
                elif api_info == "forgingdelegates":
                    return response_json["data"]
                elif api_info == "delegates" or api_info == "transactions":
                    return response_json["data"][0]
                else:
                    if api_info == "balance" or api_info == "voters":
                        return 0
                    return ""
            else:
                if api_info == "balance" or api_info == "voters":
                    return 0
                return ""
        else:
            print("Error (not 200): " + str(response.status_code) + ' URL: '
                  + request_url + ', response: ' + response.text)
            if api_info == "balance" or api_info == "voters":
                return 0
            return ""
    except:
        print("Error: url is probably not correct: " + request_url)
        # known case: with parameter 'delegates' and if there are no votes returned from API, this exception occurs
        if api_info == "balance" or api_info == "voters":
            return 0
        else:
            return ""


##############################################################################
# get_dpos_api_info_GNY
# specific for Dpos nodes and their API
# node_url: is the base of the API without the /, which is stripped earlier
# address: can be several identifications: the public address; the publickey
# api_info : indicates which part of the API we use (see the elif statement)
#

def get_dpos_api_info_gny(node_url, address, api_info):

    if api_info == "balance":
        request_url = node_url + '/api/accounts?address=' + address
    elif api_info == "delegates":
        request_url = node_url + '/api/delegates/get?address=' + address
    elif api_info == "voters":
        request_url = node_url + '/api/delegates/getVoters?username=' + address
    elif api_info == "status":
        request_url = node_url + '/api/blocks/getStatus'
    elif api_info == "blocks2":
        request_url = node_url + '/api/delegates/ownProducedBlocks?username=' + address
    else:
        return ""

    try:
        response = requests.get(request_url, timeout=10)
        if response.status_code == 200:
            response_json = response.json()

            if response_json["success"] == True:
                if api_info == "balance":
                    return response_json["account"][api_info]
                elif api_info == "voters":
                    return len(response_json["accounts"])
                elif api_info == "votes":
                    return response_json["data"]["votes"]
                elif api_info == "blocks2":
                    return response_json["blocks"]

                elif api_info == "status":
                    return response_json

                elif api_info == "forgingdelegates":
                    return response_json["data"]
                elif api_info == "delegates" or api_info == "transactions":
                    return response_json["delegate"]
                else:
                    if api_info == "balance" or api_info == "voters":
                        return 0
                    return ""
            else:
                if api_info == "balance" or api_info == "voters":
                    return 0
                return ""
        else:
            print("Error (not 200): " + str(response.status_code) + ' URL: '
                  + request_url + ', response: ' + response.text)
            if api_info == "balance" or api_info == "voters":
                return 0
            return ""
    except:
        print("Error: url is probably not correct: " + request_url)
        # known case: with parameter 'delegates' and if there are no votes returned from API, this exception occurs
        if api_info == "balance" or api_info == "voters":
            return 0
        else:
            return ""


# #############################################################################
# productivity_check
# blockchain = which chain
# recent_blocks =  last 100 blocks from the block chain
# curr_height = current height of the block chain

def productivity_check_gny(blockchain, recent_blocks, curr_height):

    # Check how much rounds are available with this call - I expect 100 in a continious situation. If less than 2; stop!
    total_rounds = len(recent_blocks)

    if total_rounds < 2:
        return 0

    missed = 0
    forged = 0

    net_round = calc_round(curr_height, blockchain)
    cur_round = calc_round(int(recent_blocks[0]['height']), blockchain)

    if net_round > cur_round + 1:
        missed += net_round - cur_round - 1
    else:
        forged += 1

    # Walk through the 100 blocks, which this delegate has forged; if delegate missed a block; the normalised blocknr is disturbed;
    for i in range(0,total_rounds - 1):
        cur_round = calc_round(int(recent_blocks[i]['height']), blockchain)
        prev_round = calc_round(int(recent_blocks[i + 1]['height']), blockchain)
        if prev_round < cur_round - 1:
            if cur_round - prev_round - 1 > total_rounds - missed - forged:
                missed += total_rounds - missed - forged
                break
            else:
                missed += cur_round - prev_round - 1
        else:
            forged += 1
    productivity = (forged * 100)/(forged + missed)
    return round(productivity)