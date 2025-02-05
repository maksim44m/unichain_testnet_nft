import os
import sys
from loguru import logger
from pathlib import Path

pk = ''
seed = ''
proxy = ''  # 'http://login:password@host:port'

nft = {'Unichain Alien (UA)': '0xAdE5aE3e71ff1E6D1E1e849d18A4DF27189a61be',
       'OROCHIMARU': '0x87787cAacb6b928eb122D761eF1424217552Ac5F',
       'Europa': '0x2188DA4AE1CAaFCf2fBFb3ef34227F3FFdc46AB6',
       'Unicorn': '0x99F4146B950Ec5B8C6Bc1Aa6f6C9b14b6ADc6256'}

DATADIR = Path(__file__).resolve().parent.parent / "data"
LOGSDIR = Path(__file__).resolve().parent.parent / "data" / "logs"
ABISDIR = Path(__file__).resolve().parent / "ABIs"

logger.remove()
logger.add(
    os.path.join(LOGSDIR, 'log.txt'),
    format="{time:DD-MM HH:mm:ss} | {level: <8} {file}:{function}:{line} | - {message}",
    level="TRACE",  # TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL
    rotation="00:00",
)

logger.add(
    sys.stdout,
    colorize=True,
    format="<white>{time:HH:mm:ss}</white> | "
           "<level>{level: <8} {file}:{function}:{line}</level> | "
           "<light-cyan>{message}</light-cyan>",
    level="INFO",
)
