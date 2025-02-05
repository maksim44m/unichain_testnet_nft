from typing import Union, Optional, Tuple
from random import uniform
from decimal import Decimal

from eth_typing import ChecksumAddress
from web3 import Web3, Account  # pip install web3
from web3.types import Wei
from web3.contract import Contract
from pydantic import BaseModel, model_validator  # pip install pydantic

from utils.config import logger, ABISDIR
from utils.reader_json import read_from_json


class Amount(BaseModel):
    amount: Union[int, float, Decimal, Wei]
    decimals: int = 18
    is_wei: bool = False

    wei: int = None
    ether: Decimal = None
    ether_float: float = None

    @model_validator(mode='before')
    def compute_values(cls, values: dict) -> dict:
        amount = values.get('amount')
        decimals = values.get('decimals', 18)
        is_wei = values.get('is_wei', False)

        if is_wei:
            wei = int(amount)
            ether = Decimal(amount) / (10 ** decimals)
        else:
            wei = int(Decimal(amount) * (10 ** decimals))
            ether = Decimal(amount)

        values['wei'] = wei
        values['ether'] = ether
        values['ether_float'] = float(ether)
        return values


class Onchain:
    def __init__(self, rpc: str, seed: str = None, pk: str = None, proxy: str = None):
        self.w3 = Web3(provider=Web3.HTTPProvider(
            endpoint_uri=rpc, request_kwargs={'proxy': proxy}))
        if pk:
            self.pk = pk
        elif not pk and seed:
            Account.enable_unaudited_hdwallet_features()
            self.pk = self.w3.eth.account.from_mnemonic(seed).key.hex()
        else:
            logger.error(f'Not init, check pk/seed')
        self.address = self.w3.eth.account.from_key(self.pk).address

    def get_contract(self, contract_address: str | None,
                     abi_name: str = 'erc20') -> Optional[Contract]:
        """Создание объекта контракта, если нет то работа с нативным токеном"""
        if not contract_address:
            return None
        contract_address = self.w3.to_checksum_address(contract_address)
        abi = read_from_json(abi_name, path=ABISDIR)
        return self.w3.eth.contract(contract_address, abi=abi)

    def get_balance(self, contract_address: str = '') -> float:
        """Запрос баланса, по умолчанию нативный токен или смарт контракт"""
        if not contract_address:
            amount = Amount(amount=self.w3.eth.get_balance(self.address),
                            is_wei=True)
            return amount.ether_float
        contract = self.get_contract(contract_address)
        decimals = contract.functions.decimals().call()
        balance = contract.functions.balanceOf(self.address).call()
        amount = Amount(amount=balance, decimals=decimals, is_wei=True)
        return amount.ether_float

    def get_fees(self) -> Tuple[int, int]:
        """
        Запрос 30 последних блоков для получения priority_fee
        + запрос base_fee и расчет max_fee
        """
        fee_history = self.w3.eth.fee_history(
            block_count=30, newest_block="latest", reward_percentiles=[20])
        base_fee = self.w3.eth.gas_price
        priority_fees = [priority_fee[0] for priority_fee in fee_history['reward']]
        priority_fees.sort()
        priority_fee = priority_fees[len(priority_fees) // 2]
        max_fee = int((base_fee + priority_fee) * self.random_multiplayer())
        return priority_fee, max_fee

    def prepare_tx(self, to_address: ChecksumAddress,
                   value: Optional[Amount] = None) -> dict:
        """
        Подготовка параметров транзакции с опциональным параметром
        value (количество нативного токена)
        """
        priority_fee, max_fee = self.get_fees()
        tx_params = {'from': self.address,
                     'to': to_address,
                     'nonce': self.w3.eth.get_transaction_count(self.address),
                     'maxPriorityFeePerGas': priority_fee,
                     'maxFeePerGas': max_fee,
                     'chainId': self.w3.eth.chain_id, }
        if value:
            tx_params['value'] = value.wei
        return tx_params

    @staticmethod
    def random_multiplayer():
        return uniform(1.15, 1.3)

    def send_transaction(self, amount: float, to_address: str | ChecksumAddress,
                         contract_address: Optional[str | ChecksumAddress] = None) -> str:
        """
        Отправка нативных токенов и токенов через вызов смарт контракта
        """
        to_address = self.w3.to_checksum_address(to_address)
        if contract_address:  # смарт контракт
            contract = self.get_contract(contract_address)
            decimals = contract.functions.decimals().call()
            amount = Amount(amount=amount, decimals=decimals)
            tx = self.prepare_tx(to_address=contract.address)
            tx['data'] = contract.encode_abi("transfer", (to_address, amount.wei))
        else:  # нативный токен
            amount = Amount(amount=amount)
            tx = self.prepare_tx(to_address=to_address, value=amount)

        return self._sign_and_create(tx)

    def send_transaction_with_abi(self, contract_address: str | ChecksumAddress,
                                  abi: str, function: str, amount: float = None,
                                  data: list = None):

        if amount:
            amount = Amount(amount=amount)

        contract_address = self.w3.to_checksum_address(contract_address)
        contract = self.get_contract(contract_address=contract_address,
                                     abi_name=abi)

        tx = self.prepare_tx(to_address=contract_address, value=amount)
        tx['data'] = contract.encode_abi(function, data)

        return self._sign_and_create(tx)

    def _sign_and_create(self, tx: dict):
        tx['gas'] = int(self.w3.eth.estimate_gas(tx) * self.random_multiplayer())

        signed_tx = self.w3.eth.account.sign_transaction(tx, self.pk)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_receipt.transactionHash.hex()

    def to_checksum(self, address: str):
        return self.w3.to_checksum_address(address)
