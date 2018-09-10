from indy import wallet, pool, did, ledger, payment
from minter.constants import *
import json
from minter.lib import load_libsovtoken
import string
import random
import os
from threading import Lock
lock = Lock()

async def create_wallet_pool_trustees(argv):
    wallet_config = json.dumps({"id": "minter"})
    wallet_creds = json.dumps({"key": "1"})
    load_libsovtoken()

    try:
        await wallet.create_wallet(wallet_config, wallet_creds)
    except:
        pass

    global wallet_id
    wallet_id = await wallet.open_wallet(wallet_config, wallet_creds)

    pool_name = 'minter_pool'
    await pool.set_protocol_version(2)
    here = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(here, 'docker_pool_transactions_genesis')
    pool_config = json.dumps({"genesis_txn": path})
    try:
        await pool.create_pool_ledger_config(pool_name, pool_config)
    except:
        pass

    global pool_id
    pool_id = await pool.open_pool_ledger(pool_name, None)

    _ = await get_vk_by_seed_and_did(SEED_1, DID_1)
    vk_2 = await get_vk_by_seed_and_did(SEED_2, DID_2)
    vk_3 = await get_vk_by_seed_and_did(SEED_3, DID_3)

    nym_req_1 = await ledger.build_nym_request(DID_1, DID_2, vk_2, None, "TRUSTEE")
    await ledger.sign_and_submit_request(pool_id, wallet_id, DID_1, nym_req_1)

    nym_req_2 = await ledger.build_nym_request(DID_1, DID_3, vk_3, None, "TRUSTEE")
    await ledger.sign_and_submit_request(pool_id, wallet_id, DID_1, nym_req_2)


async def build_mint_req(request):
    s = "".join(map(chr, await request.content.read(-1)))
    json_s = json.loads(s)

    seed = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))
    global mint_address
    mint_address = await payment.create_payment_address(wallet_id, "sov", json.dumps({"seed": seed}))

    amount = json_s.get("amount", 100)
    req, payment_method = await payment.build_mint_req(wallet_id, DID_1, json.dumps([{"recipient": mint_address, "amount": amount}]), None)

    req = await ledger.multi_sign_request(wallet_id, DID_1, req)
    req = await ledger.multi_sign_request(wallet_id, DID_2, req)
    req = await ledger.multi_sign_request(wallet_id, DID_3, req)

    resp = await ledger.submit_request(pool_id, req)

    res = {
        "seed": seed
    }
    res = {k: v for k, v in res.items() if v is not None}
    return json.dumps(res)


async def transfer_funds(request):
    s = "".join(map(chr, await request.content.read(-1)))
    json_s = json.loads(s)
    try:
        address = json_s["address"]
    except KeyError:
        raise Exception(json.dumps({"error": "No address set"}))

    amount = json_s.get("amount", 100)

    lock.acquire()
    utxo_req, method = await payment.build_get_payment_sources_request(wallet_id, DID_1, mint_address)
    utxo_resp = await ledger.submit_request(pool_id, utxo_req)
    utxo_parsed_resp = await payment.parse_get_payment_sources_response(method, utxo_resp)
    utxos_json = json.loads(utxo_parsed_resp)

    utxo_amount = 0
    utxo = None
    for utxo_struct in utxos_json:
        utxo_amount = utxo_struct.get("amount")
        if utxo_amount >= amount:
            utxo = utxo_struct.get("source")

    if utxo_amount < amount:
        lock.release()
        raise Exception(json.dumps({"error": "Not enough tokens"}))

    payment_req, method = await payment.build_payment_req(wallet_id,
                                                  DID_1,
                                                  json.dumps([utxo]),
                                                  json.dumps([
                                                      {
                                                          "recipient": address,
                                                          "amount": amount
                                                      },
                                                      {
                                                          "recipient": mint_address,
                                                          "amount": utxo_amount - amount
                                                      }
                                                  ]),
                                                  None)

    payment_resp = await ledger.submit_request(pool_id, payment_req)
    parsed_payment_resp = await payment.parse_payment_response(method, payment_resp)
    lock.release()
    return "{}"


async def get_vk_by_seed_and_did(seed, did_to_resolve):
    try:
        _, vk = await did.create_and_store_my_did(wallet_id, json.dumps({"seed": seed}))
    except:
        vk = await did.key_for_local_did(wallet_id, did_to_resolve)
    return vk