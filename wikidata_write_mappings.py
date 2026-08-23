import csv, sys, time, re
from datetime import datetime
import mwclient # Wikidata / Wikibase via mwclient
from config_private import wd_bot_user, wd_bot_pwd, wb_bot_pwd, wb_bot_user
import requests, json

# This script looks for Wikidata-links in Wikibase entities, and writes the link to Wikidata (if not already present).
# For aligned senses, in addition to the alignment, it overwrites the Wikidata gloss with the wikibase gloss (if the wikidata sense id is not in "glosses_to_leave_intact"

headers = {"User-Agent": "User:DL2204 python requests"}
# Wikidata senses with glosses manually marked as not to be overwritten with the DLP gloss
glosses_to_leave_intact = ["L448595-S1", "L450496-S1", "L473300-S2", "L670215-S1", "L500671-S1", "L448401-S1", "L447252-S1", "L473363-S1", "L471998-S1", "L472007-S1", "L473368-S1", "L500650-S2", "L474787-S1", "L661413-S1", "L8220-S1", "L447828-S1", "L447828-S2", "L669738-S1", "L450513-S1", "L447907-S1", "L447919-S2", "L738889-S1", "L584026-S1", "L307309-S1", "L483558-S1", "L448007-S1", "L477302-S1", "L226647-S1", "L500603-S1", "L584025-S1", "L524630-S1", "L477263-S2", "L448078-S1", "L448666-S1", "L448532-S1", "L447826-S1", "L524629-S1", "L1017186-S1", "L1017217-S1", "L1119434-S1", "L579858-S1", "L447760-S1", "L46828-S2", "L448654-S1", "L493197-S1", "L500620-S1", "L447196-S1", "L448603-S1", "L448506-S1", "L477298-S2", "L502866-S3", "L46815-S1", "L500836-S1", "L669888-S1", "L448082-S1", "L664608-S1", "L448005-S1", "L448124-S1", "L448059-S1", "L501787-S2", "L448276-S1", "L474547-S1", "L448589-S1", "L447204-S1", "L448452-S1", "L449761-S1", "L500859-S1", "L448457-S1", "L448509-S1", "L501543-S1", "L662640-S1", "L558167-S1", "L579673-S1", "L579860-S1", "L1531681-S1", "L448667-S4", "L447218-S1", "L477671-S1", "L1460274-S1", "L477169-S1", "L661423-S1", "L447158-S1"]

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

wikibase = mwclient.Site("illlp.wikibase.cloud")
def get_wikibase_token():
	global wikibase

	while True:
		try:
			login = wikibase.login(username=wb_bot_user, password=wb_bot_pwd)
			break
		except Exception as ex:
			print('ILLLP Wikibase login via mwclient raised error: '+str(ex))
			time.sleep(60)
	# get wikibase_token
	csrfquery = wikibase.api('query', meta='tokens')
	wikibase_token = csrfquery['query']['tokens']['csrftoken']
	print(f"Got fresh CSRF token for Wikibase.")
	return wikibase_token
wikibase_token = get_wikibase_token()

# Main #

choice = input("Download Wikidata entries and senses without DLP alignment 'Y' for download, other key for re-using saved lists.")
if choice == "Y":

	url = "https://query.wikidata.org/sparql?format=json&query=select%20%3Fwd_lexeme%20%3Fwd_sense%20where%0A%20%20%20%20%20%7B%20%3Fwd_lexeme%20dct%3Alanguage%20wd%3AQ5146.%0A%20%20%20%20%20%20%3Fwd_lexeme%20ontolex%3Asense%20%3Fwd_sense.%0A%20%20%20%20%20filter%20not%20exists%20%7B%3Fwd_sense%20wdt%3AP14752%20%5B%5D.%7D%0A%20%20%20%20%20%7D%20%0A%20%20"
	wb_r = requests.get(headers=headers, url=url)
	print(wb_r)
	senses = wb_r.json()['results']['bindings']
	with open('source/wikidata-unaligned-senses.json', 'w') as f:
		json.dump(senses, f, indent=2)
	time.sleep(.4)
	url = "https://query.wikidata.org/sparql?format=json&query=select%20%3Fwd_lexeme%20where%0A%20%20%20%20%20%7B%20%3Fwd_lexeme%20dct%3Alanguage%20wd%3AQ5146.%20%20%20%20%0A%20%20%20%20%20filter%20not%20exists%20%7B%3Fwd_lexeme%20wdt%3AP14752%20%5B%5D.%7D%0A%20%20%20%20%20%7D%20%0A%20%20"
	wb_r = requests.get(headers=headers, url=url)
	print(wb_r)
	lexemes = wb_r.json()['results']['bindings']
	with open('source/wikidata-unaligned-lexemes.json', 'w') as f:
		json.dump(senses, f, indent=2)
else:
	with open('source/wikidata-unaligned-senses.json') as f:
		senses = json.load(f)
	with open('source/wikidata-unaligned-lexemes.json') as f:
		lexemes = json.load(f)
print(f"Wikidata lexemes without DLP alignment '{len(lexemes)}'.")
print(f"Wikidata senses without DLP alignment '{len(senses)}'.")

wd_unaligned = []
for item in senses:
	wd_unaligned.append(item['wd_sense']['value'].replace("http://www.wikidata.org/entity/", ""))
wd_unaligned_lexemes = []
for item in lexemes:
	wd_unaligned.append(item['wd_lexeme']['value'].replace("http://www.wikidata.org/entity/", ""))
print(f"Total entities without alignment: '{len(wd_unaligned)}'.")

# get Wikibase lexemes and senses' Wikidata alignments with entity type and claim ID
# Query: https://tinyurl.com/2772e832
url = "https://illlp.wikibase.cloud/query/sparql?format=json&query=PREFIX%20ilwb%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fentity%2F%3E%0APREFIX%20ildp%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fdirect%2F%3E%0APREFIX%20ilp%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2F%3E%0APREFIX%20ilps%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fstatement%2F%3E%0APREFIX%20ilpq%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fqualifier%2F%3E%0APREFIX%20ilpr%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Freference%2F%3E%0APREFIX%20ilno%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fnovalue%2F%3E%0A%0Aselect%20%3Fwb_entity%20%3Ftype%20%3Fwd_st%20%3Fwd_entity%20%3Fxml_id%20%3Fgloss%20%3Fsource_date%20where%0A%0A%7B%0A%20%20%7B%20%3Fwb_entity%20dct%3Alanguage%20ilwb%3AQ3%3B%20ilp%3AP1%20%3Fwd_st.%20%3Fwd_st%20ilps%3AP1%20%3Fwd_entity.%20%3Fwb_entity%20ilp%3AP6%20%5Bilps%3AP6%20%3Fxml_id%3B%20prov%3AwasDerivedFrom%20%5Bilpr%3AP12%20%3Fsource_date%5D%5D.%20bind%20(%22entry%22%20as%20%3Ftype)%7D%0A%20%20union%0A%20%20%7B%20%3Fwb_entity%20skos%3Adefinition%20%3Fgloss%3B%20ilp%3AP1%20%3Fwd_st.%20%3Fwd_st%20ilps%3AP1%20%3Fwd_entity.%20%3Fwb_entity%20ilp%3AP6%20%5Bilps%3AP6%20%3Fxml_id%3B%20prov%3AwasDerivedFrom%20%5Bilpr%3AP12%20%3Fsource_date%5D%5D.%20%0A%20%20%20filter(lang(%3Fgloss)%3D%22pt%22)%20bind%20(%22sense%22%20as%20%3Ftype)%7D%0A%20%20%20%0A%7D%20"
wb_r = requests.get(headers=headers, url=url)
print(wb_r)
result = wb_r.json()['results']['bindings']
wb_mappings = {}
for row in result:
	wb_mappings[row['wb_entity']['value'].replace("https://illlp.wikibase.cloud/entity/", "")] = row
print(f"Got {len(wb_mappings)} lexemes and senses mapped to Wikidata.")
time.sleep(5)
choice = input("Press any key to proceed...")

count = 0
for wb_id in wb_mappings.keys():
	count += 1
	type = wb_mappings[wb_id]['type']['value']

	wd_id = wb_mappings[wb_id]['wd_entity']['value']
	if wd_id not in wd_unaligned:
		# print(f"\n[{count}/{len(wb_mappings)}] https://www.wikidata.org/entity/{wd_id} not in list of unmapped Wikidata items.")
		continue
	print(f"\n[{count}/{len(wb_mappings)}] now processing https://illlp.wikibase.cloud/entity/{wb_id} (type {type}).")
	xml_id = wb_mappings[wb_id]['xml_id']['value']
	source_date = "+" + wb_mappings[wb_id]['source_date']['value']
	print(f"Data to write: {wd_id} > {xml_id}, {source_date}")

	# Write to Wikidata
	claim_id = None
	while (not claim_id):
		try:
			request = wikidata.post('wbcreateclaim', token=wikidata_token, entity=wd_id, property="P14752", snaktype="value", value=f'"{xml_id}"',
								bot=1, summary=f"DLP alignment (manually checked).")
			if request['success'] == 1:
				claim_id = request['claim']['id']
				print(f"Created claim: {wd_id} - P14752 - {xml_id} ({wb_id})...", end=" ")
			time.sleep(.34)
		except Exception as ex:
			if 'Invalid CSRF token.' in str(ex):
				print('Wait a sec. Must get a new CSRF token...')
				wikidata_token = get_wikidata_token()
			else:
				print('Claim creation failed, will try again...\n' + str(ex))
			time.sleep(4)

	guidfix = re.compile(r'^(L\d+\-S\d+)\-')  # senses
	claim_id = re.sub(guidfix, r'\1$', claim_id)
	guidfix = re.compile(r'^(L\d+)\-([^\-$]{8})')  # lexemes
	claim_id = re.sub(guidfix, r'\1$\2', claim_id)

	refsnaks = json.dumps(
	{"P813": [{"snaktype": "value", "property": "P813",
			  "datavalue": {"type": "time", "value": {"time": source_date, "timezone": 0,
													  "before": 0,
													  "after": 0, "precision": 11,
													  "calendarmodel": "http://www.wikidata.org/entity/Q1985727"}}}]})
	while True:
		try:
			setref = wikidata.post('wbsetreference', token=wikidata_token, statement=claim_id, index=0, snaks=refsnaks, bot=1, summary="DLP xml source date.")
			if setref['success'] == 1:
				print(f'Time reference {source_date} successfully set.')
				time.sleep(.34)
			break
		except Exception as ex:
			if 'Invalid CSRF token.' in str(ex):
				print('Wait a sec. Must get a new Wikidata CSRF token...')
				time.sleep(10)
				wikidata_token = get_wikidata_token()
			else:
				print('Reference set failed, will try again...')
				print(str(ex))
			time.sleep(5)

	if type == "sense" and wd_id not in glosses_to_leave_intact:
		gloss = wb_mappings[wb_id]['gloss']['value'].replace(" ,", ",")
		glossdict = {"glosses": {"pt": {"language": "pt", "value": gloss}}}
		while True:
			try:
				request = wikidata.post('wbleditsenseelements', senseId=wd_id, data=json.dumps(glossdict), token=wikidata_token,
									summary=f"Gloss re-written from {xml_id}", bot=1)
				if request['success'] == 1:
					print(f'Success editing Sense http://www.wikidata.org/entity/{wd_id}')
					break
			except Exception as ex:
				if 'Invalid CSRF token.' in str(ex):
					print('Wait a sec. Must get a new Wikidata CSRF token...')
					time.sleep(10)
					wikidata_token = get_wikidata_token()
				else:
					print('editsense operation failed, will try again...\n' + str(ex))
					# logging.error('Description set operation '+s+' ('+lang+') '+val+' failed, will try again...', exc_info=True)
					time.sleep(4)
	print(f"Finished writing to http://www.wikidata.org/entity/{wd_id}")

	# write date of the Wikidata edit to mapping statement on Wikibase
	claim_id = wb_mappings[wb_id]['wd_st']['value'].replace("https://illlp.wikibase.cloud/entity/statement/","")
	guidfix = re.compile(r'^(L\d+\-S\d+)\-')  # senses
	claim_id = re.sub(guidfix, r'\1$', claim_id)
	guidfix = re.compile(r'^(L\d+)\-([^\-$]{8})')  # lexemes
	claim_id = re.sub(guidfix, r'\1$\2', claim_id)

	nowtime = "+" + datetime.now().isoformat()[:11] + "00:00:00Z"

	refsnaks = json.dumps(
	{"P17": [{"snaktype": "value", "property": "P17",
			  "datavalue": {"type": "time", "value": {"time": nowtime, "timezone": 0,
													  "before": 0,
													  "after": 0, "precision": 11,
													  "calendarmodel": "http://www.wikidata.org/entity/Q1985727"}}}]})
	while True:
		try:
			setref = wikibase.post('wbsetreference', token=wikibase_token, statement=claim_id, index=0, snaks=refsnaks, bot=1)
			if setref['success'] == 1:
				print(f'Time reference {nowtime} successfully set to Wikibase alignment claim on https://illlp.wikibase.cloud/entity/{wb_id}.')
				time.sleep(.34)
				break
		except Exception as ex:
			if 'Invalid CSRF token.' in str(ex):
				print('Wait a sec. Must get a new CSRF token...')
				time.sleep(10)
				wikibase_token = get_wikibase_token()
			else:
				print('Reference set failed, will try again...')
				print(str(ex))
				print(f"GUID was {claim_id}")
			time.sleep(5)

