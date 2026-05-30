import os

from dotenv import load_dotenv, set_key


database_file = 'users.db'
log_file = '/etc/ppp/log.log'
output_file = '/etc/ppp/chap-secrets'
ipsec_file = '/etc/ipsec.secrets'

multi_connect = None
multi_connect_key = 'MULTI_CONNECT'


vpn_request = None
vpn_request_key = 'USE_VPN'

token = None

def load_env():
    global multi_connect, token, vpn_request
    load_dotenv(override=True)
    multi_connect = True if os.getenv(multi_connect_key) in ('Yy') else False
    vpn_request = True if os.getenv(vpn_request_key) in ('Yy') else False
    token = os.getenv('TOKEN')

def set_key_env(key, value):
    set_key(".env", key, value, quote_mode='auto')
    load_env()

load_env()