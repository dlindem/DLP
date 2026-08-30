import csv, sys, time, re
from datetime import datetime
import mwclient  # Wikidata via mwclient
import ilwbi # Wikibase via WBI
from config_private import wd_bot_pwd, wd_bot_user
import requests, json

headers = {"User-Agent": "User:DL2204 python requests"}
nowtime = "+" + datetime.now().isoformat()[:11] + "00:00:00Z"

wikidata = mwclient.Site("www.wikidata.org")
def get_wikidata_token():
	global wikidata

	while True:
		try:
			login = wikidata.login(username=wd_bot_user, password=wd_bot_pwd)
			break
		except Exception as ex:
			print('Wikidata login via mwclient raised error: '+str(ex))
			time.sleep(60)
	# get wikidata_token
	csrfquery = wikidata.api('query', meta='tokens')
	wikidata_token = csrfquery['query']['tokens']['csrftoken']
	print(f"Got fresh CSRF token for Wikidata.")
	return wikidata_token
wikidata_token = get_wikidata_token()

def correct_claim(guid=None, value=None, xml_id=None, source_date=None):
	choice = input("*** REALLY change gender to this lexeme on Wikidata? 'Y' for Yes, other for skipping.")
	if choice != "Y":
		return
	global wikidata_token
	value = json.dumps({"entity-type": "item", "numeric-id": int(value.replace("Q", ""))})
	while True:
		try:
			results = wikidata.post('wbsetclaimvalue', token=wikidata_token, claim=guid, snaktype="value", value=value, bot=1, summary=f"imported from {xml_id}")
			if results['success'] == 1:
				print('Wikidata: Existing claim value update success.')
				break
		except Exception as ex:
			if 'Invalid CSRF token.' in str(ex):
				print('Wait a sec. Must get a new CSRF token...')
				wikidata_token = get_wikidata_token()
		else:
			print('Claim update failed... Will try again.')
			time.sleep(3)
	time.sleep(0.5)
	set_wd_ref(guid=guid, xml_id=xml_id, source_date=source_date)

def create_claim(subject=None, prop=None, value=None, xml_id=None, source_date=None):
	global wikidata_token
	jsonvalue = json.dumps({"entity-type": "item", "numeric-id": int(value.replace("Q", ""))})
	claim_id = None
	while not claim_id:
		try:
			request = wikidata.post('wbcreateclaim', token=wikidata_token, entity=subject, property=prop,
									snaktype="value", value=jsonvalue,
									bot=1, summary=f"imported from {xml_id}")
			if request['success'] == 1:
				claim_id = request['claim']['id']
				print(f"Wikidata: Created claim {subject} - {prop} - {value}...", end=" ")
			time.sleep(.34)
		except Exception as ex:
			if 'Invalid CSRF token.' in str(ex):
				print('Wait a sec. Must get a new CSRF token...')
				wikidata_token = get_wikidata_token()
			else:
				print('Claim creation failed, will try again...\n' + str(ex))
			time.sleep(4)
	set_wd_ref(guid=claim_id, xml_id=xml_id, source_date=source_date)

def remove_claim(claims=None, value=None):
	global wikidata_token
	for claim in claims:
		if claim['mainsnak']['datavalue']['value']['id'] == value:
			guid = claim['id']
			results = wikidata.post('wbremoveclaims', claim=guid, token=wikidata_token)
			if results['success'] == 1:
				print(f'Wikidata claim successfully removed: {claim['mainsnak']['property']} - {value}')
				time.sleep(1)

def set_wd_ref(guid=None, xml_id=None, source_date=None):
	global wikidata_token
	refsnaks = json.dumps(
		{"P14752": [{"snaktype":"value","property":"P14752","datavalue":{"type":"string","value":xml_id}}],
		 "P813": [{"snaktype": "value", "property": "P813",
				  "datavalue": {"type": "time", "value": {"time": source_date, "timezone": 0,
														  "before": 0,
														  "after": 0, "precision": 11,
														  "calendarmodel": "http://www.wikidata.org/entity/Q1985727"}}}]})
	while True:
		try:
			setref = wikidata.post('wbsetreference', token=wikidata_token, statement=guid, index=0, snaks=refsnaks, bot=1)
			if setref['success'] == 1:
				print(f'XML source ({xml_id}) and time reference {source_date} successfully set.')
				time.sleep(.34)
				return True
		except Exception as ex:
			if 'Invalid CSRF token.' in str(ex):
				print('Wait a sec. Must get a new CSRF token...')
				time.sleep(10)
				wikidata_token = get_wikidata_token()
			else:
				print(str(ex))
				print('Reference set failed, will try again...')
			print(str(ex))
			time.sleep(5)

# Main #
choice = input(
	"Download Wikibase-wikidata item and property mappings? 'Y' for download, other key for re-using saved mapping.")
if choice == "Y":

	url = "https://illlp.wikibase.cloud/query/sparql?format=json&query=PREFIX%20dct%3A%20%3Chttp%3A%2F%2Fpurl.org%2Fdc%2Fterms%2F%3E%0APREFIX%20wikibase%3A%20%3Chttp%3A%2F%2Fwikiba.se%2Fontology%23%3E%0APREFIX%20skos%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2F2004%2F02%2Fskos%2Fcore%23%3E%0APREFIX%20ilwb%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fentity%2F%3E%0APREFIX%20ildp%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fdirect%2F%3E%0APREFIX%20ilp%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2F%3E%0APREFIX%20ilps%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fstatement%2F%3E%0APREFIX%20ilpq%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fqualifier%2F%3E%0APREFIX%20ilpr%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Freference%2F%3E%0APREFIX%20ilno%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fnovalue%2F%3E%0A%0Aselect%20%3Fentity%20%3FentityLabel%20%3FclassLabel%20%3Fwd%20%20where%0A%0A%7B%20%3Fentity%20ildp%3AP1%20%3Fwd.%0A%20filter%20not%20exists%20%7B%3Fentity%20dct%3Alanguage%20%5B%5D.%7D%20%23%20no%20lexemes%0A%20filter%20not%20exists%20%7B%3Fentity%20skos%3Adefinition%20%5B%5D.%7D%20%23%20no%20senses%0A%20optional%20%7B%3Fentity%20ildp%3AP5%20%3Fclass.%7D%0A%20SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22en%22.%20%7D%0A%7D%20order%20by%20%3Fentity"
	wb_r = requests.get(headers=headers, url=url)
	print(wb_r)
	result = wb_r.json()['results']['bindings']
	with open('source/wikidata-mappings.json', 'w') as f:
		json.dump(result, f, indent=2)
else:
	with open('source/wikidata-mappings.json') as f:
		result = json.load(f)

wd_mapping = {}
for item in result:
	wd_mapping[item['entity']['value'].replace("https://illlp.wikibase.cloud/entity/", "")] = item['wd']['value']

print("Wikidata mapping loaded.")
# get Wikibase lexemes and senses aligned to Wikidata
# https://tinyurl.com/2aao95tk
print("Getting Wikibase aligned entities (entries and senses) from SPARQL...")
url = "https://illlp.wikibase.cloud/query/sparql?format=json&query=PREFIX%20ilwb%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fentity%2F%3E%0APREFIX%20ildp%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fdirect%2F%3E%0APREFIX%20ilp%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2F%3E%0APREFIX%20ilps%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fstatement%2F%3E%0APREFIX%20ilpq%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fqualifier%2F%3E%0APREFIX%20ilpr%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Freference%2F%3E%0APREFIX%20ilno%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fnovalue%2F%3E%0A%0Aselect%20%3Ftype%20%3Flid%20%3Fentity%20%3Fwd%20%3Fpatrolstamp%20%20where%0A%7B%0A%7B%20%3Fentity%20dct%3Alanguage%20ilwb%3AQ3%3B%20ildp%3AP1%20%3Fwd.%20bind(strafter(str(%3Fentity)%2Cstr(ilwb%3A))%20as%20%3Flid)%20bind(%22entry%22%20as%20%3Ftype)%0A%20%20optional%20%7B%3Fentity%20ildp%3AP18%20%3Fpatrolstamp.%7D%7D%20union%0A%7B%20%3Flexeme%20%20dct%3Alanguage%20ilwb%3AQ3%3B%20ontolex%3Asense%20%3Fentity.%20%3Fentity%20ildp%3AP1%20%3Fwd.%20bind(strafter(str(%3Flexeme)%2Cstr(ilwb%3A))%20as%20%3Flid)%20bind(%22sense%22%20as%20%3Ftype)%0A%20%20optional%20%7B%3Flexeme%20ildp%3AP18%20%3Fpatrolstamp.%7D%7D%0A%7D%20order%20by%20%3Flid%20"
wb_r = requests.get(headers=headers, url=url)
print(wb_r)
result = wb_r.json()['results']['bindings']
wb_entities = {}
for row in result:
	if 'patrolstamp' in row:
		if row['patrolstamp']['value'].startswith("2026-08-27"):
			print(f"Excluding entity patrolled on {row['patrolstamp']['value']}")
			continue
	if row['lid']['value'] not in wb_entities:
		wb_entities[row['lid']['value']] = [row]
	else:
		wb_entities[row['lid']['value']].append(row)
print(f"Got {len(result)} lexemes and senses aligned to Wikidata, which is data from {len(wb_entities)} lexemes.")

count = 0
previous_wd_lid = None
wd_item = None
for lid in wb_entities.keys():
	count += 1
	# if count == 2:
	# 	sys.exit()

	print(f"\n[{count}/{len(wb_entities)}] now processing entry https://illlp.wikibase.cloud/wiki/Lexeme:{lid}.")

	# get complete Wikibase item
	wb_item_r = requests.get(headers=headers,
							 url=f"https://illlp.wikibase.cloud/wiki/Special:EntityData/{lid}.json")
	wb_item = wb_item_r.json()['entities'][lid]
	source_date = wb_item['claims']['P6'][0]['references'][0]['snaks']['P12'][0]['datavalue']['value']['time']
	print(
		f"Got data for https://illlp.wikibase.cloud/wiki/Lexeme:{lid}, with {len(wb_item['senses'])} senses.")

	# go through Wikibase entities
	for row in wb_entities[lid]:
		entity = row['entity']['value'].replace("https://illlp.wikibase.cloud/entity/", "")
		entity_type = row['type']['value']
		wd_id = row['wd']['value']
		print(f"** {entity} ({entity_type}) http://www.wikidata.org/entity/{wd_id}")
		if entity_type == "sense":
			wd_lid = re.sub(r'\-S\d+$', '', wd_id)
		else:
			wd_lid = wd_id

		# get wd lexeme
		if wd_lid != previous_wd_lid:
			wd_item_r = requests.get(headers=headers,
									 url=f"https://www.wikidata.org/wiki/Special:EntityData/{wd_lid}.json")
			wd_item = wd_item_r.json()['entities'][wd_lid]
			print(f"Got data for https://www.wikidata.org/wiki/Lexeme:{wd_lid}, with {len(wd_item['senses'])} senses.")

			previous_wd_lid = wd_lid
		
		if entity_type == "entry":
			xml_id = wb_item['claims']['P6'][0]['mainsnak']['datavalue']['value']
			if "P14752" not in wd_item['claims']:
				input(f"Fatal error: No DLP external id claim in aligned entry.")
			elif len(wd_item['claims']['P14752']) > 1:
				input(f"Fatal error: More than on DLP external id claim in aligned entry.")
			elif wd_item['claims']['P14752'][0]['mainsnak']['datavalue']['value'] != xml_id:
				input(f"Fatal error: XML id in Wikibase and Wikidata do not match.")

			# lemmas
			# handle duplicate lemma problem (from bug in write_entries.py)
			if "pt-x-Q59342809" in wb_item['lemmas'] and "pt" in wb_item['lemmas']:
				if wb_item['lemmas']['pt-x-Q59342809']['value'] == wb_item['lemmas']['pt']['value']:
					del wb_item['lemmas']['pt-x-Q59342809']
			if "pt-x-Q59342809" in wb_item['lemmas'] and "pt-ao1990" in wb_item['lemmas']:
				if wb_item['lemmas']['pt-x-Q59342809']['value'] == wb_item['lemmas']['pt-ao1990']['value']:
					del wb_item['lemmas']['pt-x-Q59342809']
			lemma_change = []
			for lang, lemdict in wb_item['lemmas'].items():
				if lemdict['value'] == "[del]": # lemma deletion problem workaround
					continue
				if lang in wd_item['lemmas']:
					if wd_item['lemmas'][lang]['value'] != lemdict['value']:
						wd_item['lemmas'][lang]['value'] = lemdict['value']
						lemma_change.append(lang)
				else:
					wd_item['lemmas'][lang] = lemdict
					lemma_change.append(lang)

			if len (lemma_change) > 0:
				print(f"Will write updated lemma dictionary: {wd_item['lemmas']}")
				comment = f"Lemma for {',  '.join(lemma_change)} updated from {xml_id}"
				try:
					request = wikidata.post('wbeditentity', token=wikidata_token, id=wd_lid, data=json.dumps(wd_item),
					                        bot=1, summary=comment)
					if request['success'] == 1:
						print(f"Wikidata: Lemmas updated")
					time.sleep(.34)
				except Exception as ex:
					if 'Invalid CSRF token.' in str(ex):
						print('Wait a sec. Must get a new CSRF token...')
						wikidata_token = get_wikidata_token()
					else:
						print('Lemma update failed...\n' + str(ex))
					time.sleep(4)
				print(wd_item)

			# entry claims
			for prop in wb_item['claims']:
				if prop == "P15": # grammatical gender
					# check if lexeme has forms for two genders
					twoforms = False
					for lemclaim in wb_item['claims']['P19']:
						if "P20" in lemclaim['qualifiers']: # female form
							twoforms = True

					wd_gender = []
					gender_items = []
					for claim in wb_item['claims'][prop]:
						gender_items.append(claim['mainsnak']['datavalue']['value']['id'])
					if ("Q17" in gender_items) and ("Q18" in gender_items) and (not twoforms):
						wd_gender = ["Q18478758"]  # common of two genders
					elif ("Q17" in gender_items) and ("Q18" in gender_items) and twoforms:
						wd_gender = ["Q499327", "Q1775415"]  # masc and fem
					elif "Q17" in gender_items:
						wd_gender = ["Q499327"]  # masculine
					elif "Q18" in gender_items:
						wd_gender = ["Q1775415"]  # feminine

					wd_gender_items = []
					if "P5185" in wd_item['claims']:
						for claim in wd_item['claims']["P5185"]:
							wd_gender_items.append(claim['mainsnak']['datavalue']['value']['id'])
						for gender_to_write in wd_gender:
							if gender_to_write in wd_gender_items:
								print(f"Checked gender, {wd_gender} is ok.")
							else:
								create_claim(subject=wd_id, prop="P5185", value=gender_to_write, xml_id=xml_id,
											 source_date=source_date)
								with open('source/alignment-patrol.csv', 'a') as file:
									file.write(
										f"{entity}\thttp://www.wikidata.org/entity/{wd_id}\tP5185\t{wd_gender} (gender)\tadd\t{datetime.now().isoformat()}\n")
						for gender_to_remove in wd_gender_items:
							if gender_to_remove not in wd_gender:
								remove_claim(claims=wb_item['claims']['P5185'], value=gender_to_remove)
						if len(gender_items) > 1:
							pass
							# input(f"http://www.wikidata.org/entity/{wd_id} has more than one gender item. Check that. Any key to skip this gender statement.")
						elif len(gender_items) == 1:
							if gender_items[0] == wd_gender:
								print(f"Checked gender, {wd_gender} is ok.")
							else:
								pass
								# correct_claim(guid=wd_item['claims']["P5185"][0]['id'], value=wd_gender, xml_id=xml_id,
								#               source_date=source_date)
								# with open('source/alignment-patrol.csv', 'a') as file:
								# 	file.write(
								# 		f"{entity}\thttp://www.wikidata.org/entity/{wd_id}\tprop\t{wd_gender} (gender)\tupdate\t{datetime.now().isoformat()}\n")
					else:
						for gender_to_write in wd_gender:
							create_claim(subject=wd_id, prop="P5185", value=gender_to_write, xml_id=xml_id,
										 source_date=source_date)
							with open('source/alignment-patrol.csv', 'a') as file:
								file.write(
									f"{entity}\thttp://www.wikidata.org/entity/{wd_id}\tP5185\t{wd_gender} (gender)\tadd\t{datetime.now().isoformat()}\n")

				elif prop == "P16":
					plurale_tantum = False
					for claim in wb_item['claims'][prop]:
						if claim['mainsnak']['datavalue']['value']['id'] == "Q465":
							plurale_tantum = True
					if plurale_tantum:
						if "P1552" in wd_item['claims']:
							for claim in wd_item['claims']["P1552"]:
								if claim['mainsnak']['datavalue']['value']['id'] == "Q138246":
									print(f'Checked plurale tantum, is ok.')
									plurale_tantum = False
					if plurale_tantum:
						create_claim(subject=wd_id, prop="P1552", value="Q138246", xml_id=xml_id,
						             source_date=source_date)
						with open('source/alignment-patrol.csv', 'a') as file:
							file.write(
								f"{entity}\thttp://www.wikidata.org/entity/{wd_id}\tP1552\tQ138246 (plurale tantum)\tadd\t{datetime.now().isoformat()}\n")


		elif entity_type == "sense": # language style, location of sense use, field of use
			wb_sense = None
			wd_sense = None

			# get possible claims on entry level that on Wikidata will belong to sense (all senses in the entry)
			entry_claims_for_senses = {}
			for prop in ["P9", "P10", "P11"]:
				wd_prop = wd_mapping[prop]
				if prop in wb_item['claims']:
					if prop not in entry_claims_for_senses:
						entry_claims_for_senses[prop] = []
					for claim in wb_item['claims'][prop]:
						value = claim['mainsnak']['datavalue']['value']['id']
						entry_claims_for_senses[prop].append(value)

			for sense in wb_item['senses']:
				if sense['id'] == entity:
					wb_sense = sense
					xml_id = wb_sense['claims']['P6'][0]['mainsnak']['datavalue']['value']
					break
			for sense in wd_item['senses']:
				if sense['id'] == wd_id:
					wd_sense = sense
					if "P14752" not in wd_sense['claims']:
						input(f"Fatal error: No DLP external id claim in aligned sense.")
					elif len(wd_sense['claims']['P14752']) > 1:
						input(f"Fatal error: More than one DLP external id claim in aligned sense.")
					elif wd_sense['claims']['P14752'][0]['mainsnak']['datavalue']['value'] != xml_id:
						input(f"Fatal error: XML id in Wikibase and Wikidata do not match.")
			if not wd_sense:
				input(f"Fatal error: Did not find Wikidata sense in lexeme: {wd_id}")
			for prop in wb_sense['claims']:
				if prop in ["P9", "P10", "P11"]:
					wd_value = None
					for claim in wb_sense['claims'][prop]:
						value = claim['mainsnak']['datavalue']['value']['id']
						wd_value = wd_mapping[value]
						wd_prop = wd_mapping[prop]
						if wd_prop in wd_sense['claims']:
							for wd_claim in wd_sense['claims'][wd_prop]:
								if wd_claim['mainsnak']['datavalue']['value']['id'] == wd_value:
									print(f"Checked {wd_prop}, {value}: is ok.")
									wd_value = None
						if wd_value:
							print(f"Will create claim on Wikidata sense.")
							create_claim(subject=wd_id, prop=wd_prop, value=wd_value, xml_id=xml_id, source_date=source_date)
							with open('source/alignment-patrol.csv', 'a') as file:
								file.write(f"{entity}\thttp://www.wikidata.org/entity/{wd_id}\t{wd_prop}\t{wd_value}\tadd from sense\t{datetime.now().isoformat()}\n")
			for prop in entry_claims_for_senses:
				for value in entry_claims_for_senses[prop]:
					wd_value = wd_mapping[value]
					wd_prop = wd_mapping[prop]
					if wd_prop in wd_sense['claims']:
						for wd_claim in wd_sense['claims'][wd_prop]:
							if wd_claim['mainsnak']['datavalue']['value']['id'] == wd_value:
								print(f"Checked {wd_prop}, {value}: is ok.")
								wd_value = None
					if wd_value:
						print(f"Will create claim (from entry level) on Wikidata sense.")
						entry_xml_id = wb_item['claims']['P6'][0]['mainsnak']['datavalue']['value']
						create_claim(subject=wd_id, prop=wd_prop, value=wd_value, xml_id=entry_xml_id,
									 source_date=source_date)
						with open('source/alignment-patrol.csv', 'a') as file:
							file.write(
								f"{entity}\thttp://www.wikidata.org/entity/{wd_id}\t{wd_prop}\t{wd_value}\tadd from entry\t{datetime.now().isoformat()}\n")

	# write patrol mark to Wikibase
	wbi_item = ilwbi.wbi.lexeme.get(entity_id=lid)
	wbi_item.claims.add(ilwbi.Time(prop_nr="P18", time=nowtime, precision=11), action_if_exists=ilwbi.ActionIfExists.REPLACE_ALL)
	wbi_item.write()
	time.sleep(.2)
	print(f"Finished {lid}.")

