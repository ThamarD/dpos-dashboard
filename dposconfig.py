# Network definitions
ark_type_nodes = {
    'Ark',
    'DArk',
    'Bind main',
    'Bind dev',
    'Qredit',
    'QreditV2',
    'Blockpool',
    'Hydra',
}

lisk_type_nodes = {
    'LeaseHold',
    'Lisk main',
    'Lisk test',
}

otherdpos_type_nodes = {
    'Adamant',
    'Shift main',
    'Shift test',
    'Rise',
    'GNY test',
    'GNY main',
}

# Network Settings [#delegates / blocktime in sec. / explorer URL / node URL needed for API-calls]
networksettings = {
    'Ark': [51,          8, 'https://explorer.ark.io',           '/address/',    'http://5.196.105.32:4003/api'],
    'DArk': [51,         8, 'https://dexplorer.ark.io',          '/wallets/',    'http://52.191.185.7:4003/api'],       # thamar's node - please use your own relay node
    'Bind main': [47,    6, 'https://bindscan.io',               '/address/',    'http://46.101.255.171:4003/api'],
    'Bind dev': [47,     6, 'https://explorer.nos.dev',          '/address/',    'http://104.209.180.20:4003/api'],     # thamar's node - please use your own relay node
    'Qredit': [51,       8, 'https://explorer.qredit.io/#',      '/address/',    'https://qredit.cloud/api'],
    'QreditV2': [51,     8, 'https://explorer.sh/#',             '/address/',    'http://52.191.185.7:5103/api'],
    'Blockpool': [201,  15, 'http://bplexp.blockpool.io',        '/address/',    'http://api.mainnet.blockpool.io:9031/api'],
    'Hydra': [53,        8, 'http://hydra.iop.global/#',         '/address/',    'http://35.195.150.223:4703/api/v2'],

    # Lisk based blockchains
    'LeaseHold': [39,    10, 'https://explorer.leasehold.io',    '/address/',    'http://54.204.208.232:8010'],
    'Lisk main': [101,   10, 'https://explorer.lisknode.io',     '/address/',    'https://api.lisknode.io'],
    'Lisk test': [101,   10, 'https://testnet-explorer.lisk.io', '/address/',    'https://testnet.lisk.io'],

    # Other DPoS blockchains
    'Adamant': [101,      5, 'https://explorer.adamant.im',      '/address/',    'https://bid.adamant.im/api'],
    'Shift main': [101,  27, 'https://explorer.shiftnrg.io',     '/address/',    'https://wallet.shiftnrg.org/api'],                # Network will be shutdown soon!
    'Shift test': [101,  27, 'https://testnet.explorer.shiftnrg.io', '/address/',    'https://wallet.testnet.shiftnrg.org/api'],    # Network will be shutdown soon!
    'Rise': [250,        30, 'https://explorer.rise.vision',     '/address/',    'http://209.222.30.239:5555/api'],     # will be stopped soon and replaced by Veritise

    # Special DPoS blockchains - GNY
    'GNY test': [101,    10, 'https://testnet.explorer.gny.io',  '/account-detail?address=',    'https://testnet.gny.io'],
    'GNY main': [101,    10, 'https://explorer.gny.io',          '/account-detail?address=',    'https://mainnet.gny.io'],
}
# #####################################################################################################################
# Old not working or depricated chains/entry's
#   'Ripa': [101, 8, 'https://explorer.ripaex.io', '/address/', 'https://api.ripaex.io/api/v2'],
#   'Kapu': [51, 8, 'https://explorer.kapu.one', '/address/', 'https://api.kapunode.net/api/v2'],
#   'Bind dev': [47,     6, 'https://explorer.nos.dev',         '/address/',    'https://api.nos.dev/api'],
