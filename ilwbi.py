from config_private import wb_bot_user, wb_bot_pwd #, wd_user, wd_pwd
from wikibaseintegrator import wbi_login, WikibaseIntegrator
from wikibaseintegrator.datatypes.string import String
from wikibaseintegrator.datatypes.externalid import ExternalID
from wikibaseintegrator.datatypes.item import Item
from wikibaseintegrator.datatypes.monolingualtext import MonolingualText
from wikibaseintegrator.datatypes.time import Time
from wikibaseintegrator.datatypes.globecoordinate import GlobeCoordinate
from wikibaseintegrator.datatypes.url import URL
from wikibaseintegrator.models import Reference, References, Sense
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_helpers
from wikibaseintegrator.wbi_enums import ActionIfExists, WikibaseSnakType
from wikibaseintegrator.models.claims import Claims

# setup wbi for own wikibase
wbi_config['MEDIAWIKI_API_URL'] = 'https://illlp.wikibase.cloud/w/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://illlp.wikibase.cloud/query/sparql'
wbi_config['WIKIBASE_URL'] = 'https://illlp.wikibase.cloud'

login_instance = wbi_login.Login(user=wb_bot_user, password=wb_bot_pwd)
wbi = WikibaseIntegrator(login=login_instance)

sparql_prefixes = """
PREFIX ilwb: <https://illlp.wikibase.cloud/entity/>
PREFIX ildp: <https://illlp.wikibase.cloud/prop/direct/>
PREFIX ilp: <https://illlp.wikibase.cloud/prop/>
PREFIX ilps: <https://illlp.wikibase.cloud/prop/statement/>
PREFIX ilpq: <https://illlp.wikibase.cloud/prop/qualifier/>
PREFIX ilpr: <https://illlp.wikibase.cloud/prop/reference/>
PREFIX ilno: <https://illlp.wikibase.cloud/prop/novalue/>
"""