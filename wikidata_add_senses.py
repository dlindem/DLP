import sys, time, re
from datetime import datetime
import wdwbi  # Wikidata via WikibaseIntegrator
import ilwbi  # Wikibase via WikibaseIntegrator
import requests, json
from wikibaseintegrator.wbi_enums import ActionIfExists

headers = {"User-Agent": "david.lindemann@ehu.eus User:DL2204 python requests"}

def switch_wbi_to(bot):
	if bot == "ilwbi":
		ilwbi.wbi_config['MEDIAWIKI_API_URL'] = 'https://illlp.wikibase.cloud/w/api.php'
		ilwbi.wbi_config['SPARQL_ENDPOINT_URL'] = 'https://illlp.wikibase.cloud/query/sparql'
		ilwbi.wbi_config['WIKIBASE_URL'] = 'https://illlp.wikibase.cloud'
	elif bot == "wdwbi":
		wdwbi.wbi_config['MEDIAWIKI_API_URL'] = 'https://www.wikidata.org/w/api.php'
		wdwbi.wbi_config['SPARQL_ENDPOINT_URL'] = 'https://www.wikidata.org/sparql'
		wdwbi.wbi_config['WIKIBASE_URL'] = 'https://www.wikidata.org'

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
# get Wikibase lexemes aligned to Wikidata, and information about senses, and senses aligned to Wikidata
# Query: https://labur.eus/drvuxozt
print("Getting Wikibase lexeme data from SPARQL...")
url = "https://illlp.wikibase.cloud/query/sparql?format=json&query=PREFIX%20ilwb%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fentity%2F%3E%0APREFIX%20ildp%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fdirect%2F%3E%0APREFIX%20ilp%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2F%3E%0APREFIX%20ilps%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fstatement%2F%3E%0APREFIX%20ilpq%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fqualifier%2F%3E%0APREFIX%20ilpr%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Freference%2F%3E%0APREFIX%20ilno%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fnovalue%2F%3E%0A%0Aselect%20%3Flexeme%20%3Fsenses%20%3Fwd_lexeme%20%3Faligned_senses%20%3Falignments%0A%0Awhere%20%7B%0A%0A%7B%20SELECT%20%3Flexeme%20(count(distinct%20%3Fsense)%20as%20%3Fsenses)%20%3Fwd_lexeme%20(count(distinct%20%3Faligned_wd_sense)%20as%20%3Faligned_senses)%20(group_concat(distinct%20%3Falignment)%20as%20%3Falignments)%20%20where%0A%0A%7B%20%3Flexeme%20dct%3Alanguage%20ilwb%3AQ3%3B%20ildp%3AP1%20%3Fwd.%0A%20optional%20%7B%3Flexeme%20ontolex%3Asense%20%3Fsense.%7D%0A%20optional%20%7B%3Flexeme%20ontolex%3Asense%20%3Faligned_sense.%20%3Faligned_sense%20ildp%3AP1%20%3Faligned_wd_sense.%20bind(concat(strafter(str(%3Faligned_sense)%2Cstr(ilwb%3A))%2C%22%3A%22%2C%3Faligned_wd_sense)%20as%20%3Falignment)%7D%0A%20bind(iri(concat(str(wd%3A)%2C%3Fwd))%20as%20%3Fwd_lexeme)%0A%20%0A%7D%20group%20by%20%3Flexeme%20%3Fsenses%20%3Fwd_lexeme%20%3Faligned_senses%20%3Falignments%20%7D%0A%20%20filter(%3Fsenses%20%3E%20%3Faligned_senses)%20%7D"
wb_r = requests.get(headers=headers, url=url)
print(wb_r)
result = wb_r.json()['results']['bindings']
wb_lexemes = {}
for row in result:
	wb_lexemes[row['lexeme']['value'].replace("https://illlp.wikibase.cloud/entity/", "")] = row
print(f"Got {len(wb_lexemes)} lexemes with Wikidata alignment and more senses than aligned senses.")
time.sleep(3)

count = 0
for wb_lexeme_id, wb_data in wb_lexemes.items():
	count += 1
	# if count > 3: # to be removed for production
	#     sys.exit()
	print(f"\n[{count}/{len(wb_lexemes)}] now processing https://illlp.wikibase.cloud/entity/{wb_lexeme_id}.")
	wb_sense_count = int(wb_data['senses']['value'])
	aligned_senses_count = int(wb_data['aligned_senses']['value'])
	if aligned_senses_count == wb_sense_count: # will not occur: sparql query filters these
		print(f"All senses are aligned. Will skip this lexeme.")
		continue

	alignments = {}
	raw_alignments = wb_data['alignments']['value']
	if len(raw_alignments) > 0:
		pairs = raw_alignments.split(' ')
		for pair in pairs:
			alignments[pair.split(':')[0]] = pair.split(':')[1]

	# get complete Wikibase item
	switch_wbi_to("ilwbi")
	wb_lexeme = ilwbi.wbi.lexeme.get(entity_id=wb_lexeme_id)
	wb_item = wb_lexeme.get_json()
	entry_xml_id = wb_item['claims']['P6'][0]['mainsnak']['datavalue']['value']
	wb_lexeme_source_date = wb_item['claims']['P6'][0]['references'][0]['snaks']['P12'][0]['datavalue']['value']['time']
	print(
		f"Got data for https://illlp.wikibase.cloud/wiki/Lexeme:{wb_lexeme_id}, with {len(wb_item['senses'])} senses.")
	time.sleep(.4)
	# get wd lexeme
	wd_lexeme_id = wb_data['wd_lexeme']['value'].replace("http://www.wikidata.org/entity/", "")
	switch_wbi_to("wdwbi")
	wd_lexeme = wdwbi.wbi.lexeme.get(entity_id=wd_lexeme_id)
	time.sleep(.4)
	# get possible claims on entry level that on Wikidata will belong to sense (all senses in the entry)
	entry_claims_for_senses = {}
	for prop in ["P9", "P10", "P11"]: # language style, location of sense use, field of use
		if prop in wb_item['claims']:
			if prop not in entry_claims_for_senses:
				entry_claims_for_senses[prop] = []
			for claim in wb_item['claims'][prop]:
				value = claim['mainsnak']['datavalue']['value']['id']
				entry_claims_for_senses[prop].append(value)

	for wb_sense in wb_item['senses']:
		sense_xml_id = wb_sense['claims']['P6'][0]['mainsnak']['datavalue']['value']
		if wb_sense['id'] in alignments:
			print(f"* Sense {wb_sense['id']} is already aligned to {alignments[wb_sense['id']]}...", end=" ")
			wd_sense_xml_id = None
			for wd_s in wd_lexeme.get_json()['senses']:
				if wd_s['id'] == alignments[wb_sense['id']]:
					wd_sense_xml_id = wd_s['claims']['P14752'][0]['mainsnak']['datavalue']['value']
					break
			if wd_sense_xml_id != sense_xml_id:
				print(f"\nFatal error: Sense XML ID on Wikibase ({alignments[wb_sense['id']]}) and Wikidata ({wd_sense_xml_id}) do not match.")
				sys.exit(1)
			else:
				print(f"Sense XML ID on Wikibase and Wikidata do match. OK.")
			continue

		gloss = wb_sense['glosses']['pt']['value'].replace(" ,", "")
		new_sense = wdwbi.Sense()
		new_sense.glosses.set(language="pt", value=gloss)

		for prop in entry_claims_for_senses:
			for value in entry_claims_for_senses[prop]:
				wd_value = wd_mapping[value]
				wd_prop = wd_mapping[prop]
				references = wdwbi.References()
				reference = wdwbi.Reference()
				reference.add(wdwbi.ExternalID(prop_nr="P14752", value=entry_xml_id))
				reference.add(wdwbi.Time(prop_nr="P813", time=wb_lexeme_source_date, precision=11))
				references.add(reference)
				new_sense.claims.add(wdwbi.Item(prop_nr=wd_prop, value=wd_value, references=references), action_if_exists=wdwbi.ActionIfExists.APPEND_OR_REPLACE)

		for prop in wb_sense['claims']:
			if prop == "P6":  # DLP xml-id
				references = wdwbi.References()
				reference = wdwbi.Reference()
				reference.add(wdwbi.Time(prop_nr="P813", time=wb_lexeme_source_date, precision=11))
				references.add(reference)
				new_sense.claims.add(wdwbi.ExternalID(prop_nr="P14752", value=sense_xml_id, references=references))
			elif prop in ["P9", "P10", "P11"]: # language style, location of sense use, field of use
				wd_prop = wd_mapping[prop]
				for claim in wb_sense['claims'][prop]:
					if claim['mainsnak']['datatype'] == "wikibase-item":
						wd_value = wd_mapping[claim['mainsnak']['datavalue']['value']['id']]
						references = wdwbi.References()
						reference = wdwbi.Reference()
						reference.add(wdwbi.ExternalID(prop_nr="P14752", value=sense_xml_id))
						reference.add(wdwbi.Time(prop_nr="P813", time=wb_lexeme_source_date, precision=11))
						references.add(reference)
						new_sense.claims.add(wdwbi.Item(prop_nr=wd_prop, value=wd_value, references=references),
											 action_if_exists=ActionIfExists.APPEND_OR_REPLACE)



		wd_lexeme.senses.add(new_sense)
		print(f"+ Sense {wb_sense['id']} has been added as new sense to the lexeme.")
	try:
		switch_wbi_to("wdwbi")
		wd_lexeme.write(summary="Added new senses from DLP dictionary")
		print(f"Successfully written to https://www.wikidata.org/wiki/Lexeme:{wd_lexeme.id}")
		time.sleep(.4)
	except:
		print(f"Error writing to Wikidata. Skipping entry.")
		continue

	# write sense mappings to Wikibase
	nowtime = "+" + datetime.now().isoformat()[:11] + "00:00:00Z"
	references = ilwbi.References()
	reference = ilwbi.Reference()
	reference.add(ilwbi.Time(prop_nr="P17", time=nowtime, precision=11),
				  action_if_exists=ilwbi.ActionIfExists.REPLACE_ALL)
	references.add(reference)
	qualifiers = [ilwbi.String(prop_nr="P14", value="added to existing Wikidata lexeme")]

	wd_senses = wd_lexeme.get_json()['senses']
	for wd_sense in wd_senses:
		if "P14752" in wd_sense['claims']:
			wd_sense_id = wd_sense['id']
			xml_id = wd_sense['claims']['P14752'][0]['mainsnak']['datavalue']['value']
			for wb_sense in wb_item['senses']:
				wb_sense_id = wb_sense['id']
				if wb_sense['claims']['P6'][0]['mainsnak']['datavalue']['value'] == xml_id and wb_sense_id not in alignments:
					# write mapping information to Wikibase
					wb_lexeme.senses.get(id=wb_sense_id).claims.add(
					ilwbi.ExternalID(prop_nr="P1", value=wd_sense_id, qualifiers=qualifiers, references=references), action_if_exists=ilwbi.ActionIfExists.REPLACE_ALL)
	switch_wbi_to("ilwbi")
	wb_lexeme.write(summary="Add Wikidata mappings and Wikidata edit dates")
	print(f"Success writing new mappings to https://illlp.wikibase.cloud/entity/{wb_lexeme.id}")
	time.sleep(.12)