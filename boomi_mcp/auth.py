import os
from dotenv import load_dotenv, find_dotenv
from boomi import Boomi

def get_client() -> Boomi:
    """Initialize and return a Boomi SDK client."""
    load_dotenv(find_dotenv(usecwd=True))
    return Boomi(
        account=os.environ["BOOMI_ACCOUNT"],
        user=os.environ["BOOMI_USER"],
        secret=os.environ["BOOMI_SECRET"],
    )
