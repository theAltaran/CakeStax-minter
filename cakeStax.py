import os
import json
import asyncio
import logging
from decimal import Decimal
from urllib.request import urlopen, Request
from web3 import Web3
from web3.middleware import geth_poa_middleware

# Setup logging
log_format = '%(levelname)s:%(asctime)s: %(message)s'

logging.basicConfig(level=logging.INFO,format=log_format)

"""" Add your wallet's private Key """

logging.info('Reading config')

your_wallet_key = 'insertYourKeyHere'
rpc_uri = 'https://bsc-dataseed3.ninicoin.io/'
seekContract = '0xc27732fE1b810985c0BCD3Bf9ecd0A5e6614f8A6'
MinHatch = 0.1
PollSeconds = 60

compound_pct = Decimal('.01')

abiPolygon = '[{"constant":true,"inputs":[],"name":"ceoAddress","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"getMyMiners","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"getBalance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"initialized","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"rt","type":"uint256"},{"name":"rs","type":"uint256"},{"name":"bs","type":"uint256"}],"name":"calculateTrade","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"eth","type":"uint256"},{"name":"contractBalance","type":"uint256"}],"name":"calculateEggBuy","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"marketEggs","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[],"name":"sellEggs","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"amount","type":"uint256"}],"name":"seedMarket","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"amount","type":"uint256"}],"name":"devFee","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"pure","type":"function"},{"constant":false,"inputs":[{"name":"ref","type":"address"}],"name":"hatchEggs","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"getMyEggs","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"ref","type":"address"},{"name":"amount","type":"uint256"}],"name":"buyEggs","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"}],"name":"lastHatch","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"}],"name":"claimedEggs","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"}],"name":"hatcheryMiners","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"EGGS_TO_HATCH_1MINERS","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"eth","type":"uint256"}],"name":"calculateEggBuySimple","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"eggs","type":"uint256"}],"name":"calculateEggSell","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"}],"name":"referrals","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"ceoAddress2","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"adr","type":"address"}],"name":"getEggsSinceLastHatch","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"inputs":[],"payable":false,"stateMutability":"nonpayable","type":"constructor"}]'

"""" No need to touch anything after this """

precision = Decimal(1e18)
web3 = Web3(Web3.HTTPProvider(rpc_uri))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

def fetch_abi(contract):
    if not os.path.exists('contracts'):
        os.mkdir('./contracts')

    filename = f'contracts/{contract}.json'
    if os.path.exists(filename):
        with open(filename, 'r') as abi_file:
            abi = abi_file.read()
            logging.info('found abi file')
    else:
        logging.info('Loading abi from bscscan to save as file')
        # TODO: Error handling
		
        url = 'https://api.bscscan.com/api?module=contract&action=getabi&address=' + contract
        abi_response = urlopen(Request(url, headers={'User-Agent': 'Mozilla'})).read().decode('utf8')
        abi = json.loads(abi_response)['result']
		# polygonscan api is busted at the moment so just copy the abi json in to the variable
        #abi = json.loads(abiPolygon)['result']
        logging.info('Loaded abi from bscscan')

    with open(filename, 'w') as abi_file:
        abi_file.write(abi)

    return json.loads(abi)

def execute_transaction(call, target_account):
    logging.info(f'\texecute_transaction call={call}, target_account={target_account}')
    nonce = web3.eth.getTransactionCount(target_account.address)
    build = call.buildTransaction({'from': target_account.address, 'nonce': nonce, 'gasPrice': 5000000000})
    sign = target_account.sign_transaction(build)

    args = dict(zip([x['name'] for x in call.abi['inputs']], call.args))
    print(f'{target_account.address}: {call.address} {call.fn_name} with args {str(args)}')
    transaction = web3.eth.sendRawTransaction(sign.rawTransaction)
    if transaction:
        return transaction

account = web3.eth.account.from_key(your_wallet_key)

logging.info(f'\tMy Account: {account.address}')

""" Get the ABI for the existing contracts on BSC"""
pit_address = seekContract
pit_abi = fetch_abi(pit_address)

pit = web3.eth.contract(pit_address, abi=pit_abi)
#deposit = pit.functions.userInfo(0, account.address).call()[0]
miners = pit.functions.cakeMiners(account.address).call()
logging.info(f'\tMy current bunnies: {miners}')

async def check_for_compound(poll_interval):
    global deposit
    while True:
        pending = pit.functions.getCakeSinceCakeBake(account.address).call()
        pending = pending / 100000000
        
        #logging.info(f'\tMy current bunnies: {miners}')
        # if pending / deposit < compound_pct:
        #logging.info(f'\tPending amount: {pending}')
        if pending < MinHatch:
            logging.info(f'\tPending [{pending}] less than min [{MinHatch}]')
        else:
            run_compound = pit.functions.compoundCake(account.address)
            # run_compound = pit.functions.enterStaking(pending)
            txn = execute_transaction(run_compound, account)

            print(web3.eth.waitForTransactionReceipt(txn))
            #deposit += pending
            miners = pit.functions.cakeMiners(account.address).call()
            logging.info(f'\tMy current bunnies: {miners}')
            
        await asyncio.sleep(poll_interval)

event_handler = asyncio.get_event_loop()

try:
    event_handler.run_until_complete(check_for_compound(PollSeconds))
except KeyboardInterrupt:
    pass
