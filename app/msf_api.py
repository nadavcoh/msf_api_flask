from flask import g, current_app, session
from authlib.integrations.flask_client import OAuth

# Configuration
#OAUTH_CLIENT_ID = os.environ.get("OAUTH_CLIENT_ID", None)
#OAUTH_CLIENT_SECRET = os.environ.get("OAUTH_CLIENT_SECRET", None)
OAUTH_DISCOVERY_URL = (
    "https://hydra-public.prod.m3.scopelypv.com/.well-known/openid-configuration"
)
API_KEY = r'17wMKJLRxy3pYDCKG5ciP7VSU45OVumB2biCzzgw'
API_SERVER = "https://api.marvelstrikeforce.com"

    # OAuth 2 client setup
    #client = WebApplicationClient(GOOGLE_CLIENT_ID)
oauth = OAuth(current_app)


def _compliance_fixes(session):
    def _add_header(url, headers, body):
        headers.update({'x-api-key' : API_KEY})
        return url, headers, body
    session.register_compliance_hook('protected_request', _add_header)

def update_token(token, refresh_token=None, access_token=None):
    # https://docs.authlib.org/en/latest/client/frameworks.html#auto-update-token
    item = session["token"]
    # update old token
    item["access_token"] = token['access_token']
    item["refresh_token"] = token.get('refresh_token')
    item["expires_at"] = token['expires_at']
    session["token"] = item

oauth.register(
    'msf_api',
#   client_id = OAUTH_CLIENT_ID,
#   client_secret = OAUTH_CLIENT_SECRET,
    server_metadata_url = OAUTH_DISCOVERY_URL,
    api_base_url = API_SERVER,
#    redirect_uri = REDIRECT_URI,
    compliance_fix=_compliance_fixes,
    # https://github.com/authlib/demo-oauth-client/blob/master/flask-twitter-tool/app.py
    fetch_token=lambda: session.get('token'),
    update_token=update_token,
    client_kwargs = {'scope': 'm3p.f.pr.pro m3p.f.pr.ros m3p.f.pr.inv m3p.f.pr.act openid offline'})
#    msf_api.headers.update({'x-api-key' : API_KEY})

def get_msf_api():
    if 'msf_api' not in g:
        g.msf_api = oauth.msf_api
    return g.msf_api