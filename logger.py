import logging
import os
from dotenv import load_dotenv

load_dotenv()

NIVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, NIVEL, logging.INFO),
    format="%(asctime)s  [%(levelname)s]  %(name)s  —  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),  # exibe no terminal
    ]
)

def get_logger(nome: str) -> logging.Logger:
    return logging.getLogger(nome)