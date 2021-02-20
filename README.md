# DPoS Node Dashboard
[![MIT License](http://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/dutchpool/cdashboard/blob/master/LICENSE)
[![docs](https://img.shields.io/badge/doc-online-blue.svg)](https://github.com/dutchpool/cdashboard/wiki)


Dashboard for DPoS Node information.

An overview of all your important DPoS Node and delegate/validator information in one place! 


DPoS Node Dashboard features:
- Monitor your delegate(s) balance, rank, votes received, weight, forged status, blocks forged in 24h and Missed blocks
- Monitor your delegate(s) performance and status over the last 24 hours, balance change, rank change, votes change, weight change
- See quickly if your node is currently missing blocks or is already recovered 
- When blocks are now and then missing, this is an indicator that something could be wrong with the server 
- No need to insert secrets!!! No Pass phrases!!! in the config file! All this is done with public available information, addresses of the wallets/delegate(s)and the API's available in the several DPoS platforms
- No need to run this script on a delegate's node/server! Every server/VPS with python will do.
- Alerting via Telegram, based on a 10 min interval: Delegate missing blocks; Delegate is out of the top of the forging delegates; Explorer/wallet problems
- Able to switch monitoring on/off.
- Keep track of a history of several months by showing daily samples of the statistics.


If you want to see a working demo of the Dpos-node-dashboard, please visit: http://dposdashboarddemo.thamar.net/
If you like this dashboard created by delegate Thamar, please consider to vote for all the Dutch Pool delegates: "dutch_pool", "st3v3n", "kippers", "fnoufnou" and off course "thamar"! A small donation is also appreciated (see for more donation info below)

_More info about Dutch Pool, our mission, our other tools and contributions to the DPoS ecosystem, please visit http://dutchpool.io_


## Installing the software

First clone the crypto dashboard repository, install python and requests:

```git clone https://github.com/ThamarD/dpos-dashboard```

```cd dpos-dashboard```

```apt-get install python3-pip```

```pip3 install requests```


## Configure the software

To configure the Dashboard we need to fill in the configuration file. With this install 
you get an template json config_template.json with all the supported DPoS nodes, which you can copy and fill in. 
Here are the steps (all in the DPoS-Dashboard directory): 

```
cd ~/dpos-dashboard
cp config_template.json config.json
nano config.json
```

_Note: Never fill in your private keys, this software doesn't need those, we only work with public addresses!!!_

The parameters in the config.json:
- logfile: the file where all gathered node info is stored; default "cdashboard.json"; you can change the logfile name the way you like (handy for setting up multiple config files with multiple log files, using one python script)
- cryptodashboard_file_version: internal check if version is correct for updates
- crunch_history: true or false; this will crunch the log file after 48 hours to only one sample a day; if false, you keep every sample, which is not advisable (and not tested).
-  telegram_settings:
  - use_telegram: true or false
  - bot_key: "your-bot_key" (looks like: 340346133:AAGADFd4334YASONIC8yX4yiC0fM345kkrjweVE)
  - chat_id: "12345678"  
- coins: section where the node info is represented for each DPoS environment
  - id: unique internal identifier, can be any random name, can hold white spaces 
  - pubaddress: the public address of the delegate wallet (no need / never add your private address/seeds!!!)
  - viewtype: option is: dpos_delegate; other options are not yet implemented
  - monitoring: options are: 
    - yes: every 10 minutes this entry will be sampled and if something is wrong, and telegram is configured, you will be infomred
    - no: every 60 minutes this enty is monitored and if something is wrong, you won't be informed via telegram
  - action: options are
    - "": this entry will be handeld normaly
    - template: this entry will be ignord, no output entry will be made in the dashboard 
    - remove: remove this entry from the dashboard (cdashboard.json file); not from the config.json file
    - skip: this entry will be skipped; used when you want to pauze the active monitoring

Example config.json:
```
{
  "logfile": "cdashboard.json",
  "cryptodashboard_file_version": 0.98,
  "crunch_history": true,
  "telegram_settings": {
    "use_telegram": true,
    "bot_key": "your-bot_key",
    "chat_id": "12345678"
  },
  "coins": {
    "Bind main": [
        {
          "id": "BND bindfarm m",
          "pubaddress": "cc4Gxs9QBzWiupDs7JwVyhBkyEuCrhTYZT",
          "viewtype": "dpos_delegate",
          "monitoring": "yes",
          "action": ""
        }
    ],
    "GNY test": [
        {
          "id": "GNY Yaroo t",
          "pubaddress": "G36kSbMGtu5LijQ4yEFT3D7re6sjM",
          "viewtype": "dpos_delegate",
          "monitoring": "yes",
          "action": ""
        }
    ]
 }
}
```
Above is an example of how the config.json must looks like (removed other template DPoS entry's).

### Frontend setup:
- install and setup a webserver (apache/nginx) to serve folder web, see file ```cdashboard_site_setup.md``` 
- We advise to run the Dashboard software (python script) every 10 minutes to collect it's data and monitor.
  - we have included a bash script, ```start.sh```, which does the steps to run and copy the necessary items each time. 
  - To configure this in the crontab, crontab runs every 10 minutes 
    - ```crontab -e```
    -  ```*/10 * * * * cd ~/dpos-dashboard && bash start.sh > /dev/null 2>&1```


### Start it:

```python3 cryptodashboard.py``` or use ```bash start.sh```

or if you want to use another config file:

```python3 cryptodashboard.py -c config2.json```

It produces a file (default) "cdashboard.json" with all the crypto dashboard information which can be presented 
with the included HTML setup. Note: the 24h information will first show as blank's and will appear after 24h.


## Command line usage

```
usage: cryptodashboard.py [-h] [-c config.json] [-y]

Crypto dashboard script

optional arguments:
  -h, --help            show this help message and exit
  -c config.json        set a config file (default: config.json)

```


## Supported/tested chains / explorers

At the moment CryptDashboard supports and is tested on the following chains / explorers:
- DPoS (mainnet and testnet):  
  - ARK based chains: ARKv2.x en v3, Compendia/Bind,  Qredit v1 en v2, Blockpool, Hydra
  - Lisk based chains: Lisk, LeaseHold
  - Other based chains: Shift, Rise, Adamant


## Changelog

###### Release 0.98
- Complete rework!
  - removed/disabled the views of DPoS wallets, BTC/Alt coin wallets; will be activated later on
  - Added Various DPoS node types: GNY; ARKv3; Qreditv2 
  - Added Telegram
  - Added monitoring of missed blocks and based on this Telegram notifications!
  - Rework of design (Bootstrap 5 - use of badge's etc)
  - Changes in Rank and Votes are indicated with badges
  - Show voting weight; Large numbers are shortend 
  - rework the config.json to fill in only needed info
  - make it possible to remove info/history from an inactive address


## To Do
We are planning to integrate other cool features:
- first see how things are working out

## Donations

Besides voting for de Dutch Pool delegates, if you like this DPoS Node Dashboard and it helps you 
to get organized, we would greatly appreciate if you would consider to show some support by donating to one 
of the below mentioned addresses.

- ETH    0x7E1B5CAf074e0AB5B8aA8d7373e2756Ca105e707
- Shift: 18040765904662116201S
- Lisk:  8890122000260193860L
- BTC: 	 1NrA8k8wNRwEZj2ooKQEf2fFnF6KqTE32T


## Cr3dits

Thanks @st3v3n, @kippers, @fnoufnou for your help creating and testing this project! 
@dakk for the inspiration for the architecture of the project.
@goose for the inspiration for the productivity calculations of an ARK based node


## License

```
Copyright (c) 2021 Thamar proud member of Dutch Pool

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NON INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
```
