from config_private import wd_bot_user, wd_bot_pwd
from wikibaseintegrator import wbi_login, WikibaseIntegrator
# from wikibaseintegrator.datatypes.string import String
from wikibaseintegrator.datatypes.externalid import ExternalID
from wikibaseintegrator.datatypes.item import Item
# from wikibaseintegrator.datatypes.monolingualtext import MonolingualText
from wikibaseintegrator.datatypes.time import Time
# from wikibaseintegrator.datatypes.globecoordinate import GlobeCoordinate
from wikibaseintegrator.datatypes.url import URL
from wikibaseintegrator.models import Reference, References, Form, Sense
from wikibaseintegrator.wbi_config import config as wbi_config
# from wikibaseintegrator import wbi_helpers
# from wikibaseintegrator.wbi_enums import ActionIfExists, WikibaseSnakType
from wikibaseintegrator.models.claims import Claims
import time


# setup wbi for wikidata as wdi
wbi_config['MEDIAWIKI_API_URL'] = 'https://www.wikidata.org/w/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://www.wikidata.org/sparql'
wbi_config['WIKIBASE_URL'] = 'https://www.wikidata.org'
wbi_config['USER_AGENT'] = "User DL2204bot david.lindemann@ehu.eus"
wbi_config['MAXLAG'] = 25


login_instance = wbi_login.Login(user=wd_bot_user, password=wd_bot_pwd)
wbi = WikibaseIntegrator(login=login_instance)

print("Wikidata WBI bot loaded.")
time.sleep(.5)
