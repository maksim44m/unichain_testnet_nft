import os
from random import randint
from time import sleep

from dotenv import load_dotenv

from utils.config import logger, nft
from onchain import Onchain


def sepolia_bridge():
    sepolia = Onchain(rpc='https://1rpc.io/sepolia',  # 'https://ethereum-sepolia-rpc.publicnode.com'
                      seed=os.getenv('seed'), pk=os.getenv('pk'), proxy=os.getenv('proxy'))

    min_gas_limit = 200000
    extra_data_bytes = bytes.fromhex('7375706572627269646765')
    raw_data = [sepolia.address, min_gas_limit, extra_data_bytes]

    contract_address = '0xea58fcA6849d79EAd1f26608855c2D6407d54Ce2'
    contract_abi = 'L1StandardBridge.json'
    func = "bridgeETHTo"
    resp = sepolia.send_transaction_with_abi(contract_address=contract_address,
                                             amount=0.001,
                                             abi=contract_abi,
                                             function=func,
                                             data=raw_data)
    logger.info(f'sepolia_bridge: {resp}')


def unichain_claim(contract_address: str):
    unichain = Onchain(rpc='https://1301.rpc.thirdweb.com/',  # 'https://sepolia.unichain.org/'
                       seed=os.getenv('seed'), pk=os.getenv('pk'), proxy=os.getenv('proxy'))

    balance = unichain.get_balance()
    for i in range(10):
        if balance >= 0.00001:
            break
        sleep(randint(3, 5))
        balance = unichain.get_balance()

    receiver = unichain.address
    quantity = 1
    currency = unichain.to_checksum('0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee')
    pricePerToken = 0
    data = b''

    proof = []
    quantityLimitPerWallet = 0
    pricePerToken_proof = 2 ** 256 - 1  # uint256 (максимальное значение)
    currency_proof = unichain.to_checksum('0x0000000000000000000000000000000000000000')
    allowlistProof = (proof, quantityLimitPerWallet, pricePerToken_proof, currency_proof)

    raw_data = [receiver, quantity, currency, pricePerToken, allowlistProof, data]

    contract_abi = 'OpenEditionERC721.json'
    func = "claim"

    resp = unichain.send_transaction_with_abi(contract_address=contract_address,
                                              abi=contract_abi,
                                              function=func,
                                              data=raw_data)
    logger.info(f'unichain_claim: {resp}')


def main():
    load_dotenv()
    sepolia_bridge()
    unichain_claim(nft['OROCHIMARU'])


if __name__ == '__main__':
    main()
