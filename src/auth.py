import os
from dotenv import load_dotenv
from boomi import Boomi

def _load_env() -> None:
    load_dotenv(dotenv_path='.env', override=False)

def get_client() -> Boomi:
    """Initialize and return a Boomi SDK client."""
    _load_env()
    return Boomi(
        account=os.environ["BOOMI_ACCOUNT"],
        user=os.environ["BOOMI_USER"],
        secret=os.environ["BOOMI_SECRET"],
    )
