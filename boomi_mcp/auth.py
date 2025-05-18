import os
from boomi import Boomi

def get_client() -> Boomi:
    """Initialize and return a Boomi SDK client."""
    return Boomi(
        account=os.environ["BOOMI_ACCOUNT"],
        user=os.environ["BOOMI_USER"],
        secret=os.environ["BOOMI_SECRET"],
    )
