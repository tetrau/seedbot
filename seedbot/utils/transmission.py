from ..core.config import get_config
import transmissionrpc


def get_transmission_client():
    config = get_config()
    return transmissionrpc.Client(address=config.get('transmission_address'),
                                  port=config.get('transmission_port'),
                                  user=config.get('transmission_username'),
                                  password=config.get('transmission_password'))
