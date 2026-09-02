import csv, sys, time, re
from datetime import datetime
import ilwbi # Wikibase via WikibaseIntegrator
import wdwbi # Wikidata via WikibaseIntegrator
import requests, json
headers = {"User-Agent": "User:DL2204 python requests"}


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

choice = input("Download Wikibase-wikidata item and property mappings? 'Y' for download, other key for re-using saved mapping.")
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

# get Wikibase lexemes (no acronyms, no redirect entries) without aligned Wikidata lexeme (now set to limit 1)
# https://tinyurl.com/2cvkjvdd
# url = "https://illlp.wikibase.cloud/query/sparql?format=json&query=PREFIX%20ilwb%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fentity%2F%3E%0APREFIX%20ildp%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fdirect%2F%3E%0APREFIX%20ilp%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2F%3E%0APREFIX%20ilps%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fstatement%2F%3E%0APREFIX%20ilpq%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fqualifier%2F%3E%0APREFIX%20ilpr%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Freference%2F%3E%0APREFIX%20ilno%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fnovalue%2F%3E%0A%0Aselect%20%3Flexeme%20%3Fxml_id%20%3Fsource_date%20%20where%0A%0A%7B%20%3Flexeme%20ildp%3AP3%20ilwb%3AQ5%3B%20dct%3Alanguage%20ilwb%3AQ3%3B%20ilp%3AP6%20%5Bilps%3AP6%20%3Fxml_id%3B%20prov%3AwasDerivedFrom%20%5Bilpr%3AP12%20%3Fsource_date%5D%5D.%0A%20filter%20not%20exists%20%7B%3Flexeme%20ildp%3AP1%20%3Fwd_lexeme.%7D%20filter%20not%20exists%7B%3Flexeme%20ildp%3AP16%20ilwb%3AQ19.%7D%20filter%20not%20exists%7B%3Flexeme%20ildp%3AP16%20ilwb%3AQ22.%7D%0A%0A%7D%20"
# wb_r = requests.get(headers=headers, url=url)
# print(wb_r)
# result = wb_r.json()['results']['bindings']

query = ilwbi.sparql_prefixes + """
select ?lexeme ?xml_id ?source_date  where

{ ?lexeme ildp:P3 ilwb:Q5; dct:language ilwb:Q3; ilp:P6 [ilps:P6 ?xml_id; prov:wasDerivedFrom [ilpr:P12 ?source_date]].
 filter not exists {?lexeme ildp:P1 ?wd_lexeme.} filter not exists{?lexeme ildp:P16 ilwb:Q19.} filter not exists{?lexeme ildp:P16 ilwb:Q22.} filter not exists{?lexeme ildp:P16 ilwb:Q22.}

} limit 20000"""
result = ilwbi.wbi_helpers.execute_sparql_query(query, user_agent="User:DavidL python requests", endpoint="https://illlp.wikibase.cloud/query/sparql")['results']['bindings']
wb_lexemes = {}
for row in result:
	wb_lexemes[row['lexeme']['value'].replace("https://illlp.wikibase.cloud/entity/", "")] = row
print(f"Got {len(wb_lexemes)} lexemes without Wikidata alignment.")
time.sleep(2)

count = 0
for wb_lexeme_id in wb_lexemes:
	count += 1
	print(f"\n[{count}/{len(wb_lexemes)}] now processing https://illlp.wikibase.cloud/entity/{wb_lexeme_id}.")
	wb_lexeme_source_date = wb_lexemes[wb_lexeme_id]['source_date']['value']
	xml_id = wb_lexemes[wb_lexeme_id]['xml_id']['value']

	switch_to("ilwbi")
	wb_lexeme = ilwbi.wbi.lexeme.get(entity_id=wb_lexeme_id)
	wb_item = wb_lexeme.get_json()
	print(f"Got data for https://illlp.wikibase.cloud/wiki/Lexeme:{wb_lexeme_id}, with {len(wb_item['senses'])} senses.")
	language = wd_mapping[wb_item['language']]
	lexical_category = wd_mapping[wb_item['lexicalCategory']]
	if "P19" not in wb_item['claims']:
		continue
	# build new lexeme
	switch_wbi_to("wdwbi")
	wd_lexeme = wdwbi.wbi.lexeme.new(language=language, lexical_category=lexical_category)

	# write lemmata
	for lemlang, lemdict in wb_item['lemmas'].items():
		if lemdict['value'] == "[del]":
			continue
		wd_lexeme.lemmas.set(language=lemlang, value=lemdict['value'])
		print(f"Set lemma for {lemlang}: '{lemdict['value']}'")

	# process claims
	references = wdwbi.References()
	reference = wdwbi.Reference()
	reference.add(wdwbi.ExternalID(prop_nr="P14752", value=xml_id))
	reference.add(wdwbi.Time(prop_nr="P813", time=wb_lexeme_source_date, precision=11))
	references.add(reference)

	p6_references = wdwbi.References()
	p6_reference = wdwbi.Reference()
	p6_reference.add(wdwbi.Time(prop_nr="P813", time=wb_lexeme_source_date, precision=11))
	p6_references.add(p6_reference)

	wb_lexeme_claims = wb_item['claims']
	entry_claims_for_senses = []

	for prop in wb_lexeme_claims:
		if prop == "P6": # DLP xml-id
			if wb_lexeme_claims[prop][0]['mainsnak']['datavalue']['value'] != xml_id:
				print(f"Fatal error: Source list xml_id does not match to lexeme xml_id: {xml_id}")
				sys.exit()

			wd_lexeme.claims.add(wdwbi.ExternalID(prop_nr="P14752", value=xml_id, references=p6_references))
			print(f"Entry level DLP alignment claim set: P14752 > {xml_id}")

		elif prop == "P15":  # grammatical gender
			# check if lexeme has forms for two genders
			twoforms = False
			for lemclaim in wb_item['claims']['P19']:
				if "qualifiers" in lemclaim:
					if "P20" in lemclaim['qualifiers']:
						twoforms = True

			wd_genders = []
			wb_gender_items = []
			for claim in wb_item['claims'][prop]:
				wb_gender_items.append(claim['mainsnak']['datavalue']['value']['id'])
			if ("Q17" in wb_gender_items) and ("Q18" in wb_gender_items) and (not twoforms):
				wd_genders = ["Q18478758"]  # common of two genders
			elif ("Q17" in wb_gender_items) and ("Q18" in wb_gender_items) and twoforms:
				wd_genders = ["Q499327", "Q1775415"] # masc and fem
			elif "Q17" in wb_gender_items:
				wd_genders = ["Q499327"]  # masculine
			elif "Q18" in wb_gender_items:
				wd_genders = ["Q1775415"]  # feminine
			for wd_gender in wd_genders:
				wd_lexeme.claims.add(wdwbi.Item(prop_nr="P5185", value=wd_gender, references=references),
								 action_if_exists=wdwbi.ActionIfExists.APPEND_OR_REPLACE)
				print(f"Gender claim added: {wd_gender}. Twoforms = {twoforms}")
		elif prop == "P16": # plurale tantum
			for claim in wb_item['claims'][prop]:
				if claim['mainsnak']['datavalue']['value']['id'] == "Q465":
					wd_lexeme.claims.add(wdwbi.Item(prop_nr="P1552", value="Q138246", references=references), action_if_exists=wdwbi.ActionIfExists.REPLACE_ALL)
					print("Plurale tantum characteristic added.")
		elif prop in ['P9', 'P10', 'P11']: # language style, location of sense use, field of use
			wd_prop = wd_mapping[prop]
			# add these entry-level claims to all senses
			for claim in wb_lexeme_claims[prop]:
				claim_value = claim['mainsnak']['datavalue']['value']['id']
				if claim_value not in wd_mapping:
					continue
				wd_value = wd_mapping[claim_value]
				entry_claims_for_senses.append(wdwbi.Item(prop_nr=wd_prop, value=wd_value, references=references))

	# build senses from scratch

	for sense in wb_item['senses']:
		gloss = sense['glosses']['pt']['value']
		new_sense = wdwbi.Sense()
		new_sense.glosses.set(language="pt", value=gloss)
		sense_xml_id = sense['claims']['P6'][0]['mainsnak']['datavalue']['value']

		references = wdwbi.References()
		reference = wdwbi.Reference()
		reference.add(wdwbi.ExternalID(prop_nr="P14752", value=sense_xml_id))
		reference.add(wdwbi.Time(prop_nr="P813", time=wb_lexeme_source_date, precision=11))
		references.add(reference)

		new_sense.claims.add(wdwbi.ExternalID(prop_nr="P14752", value=sense_xml_id, references=p6_references))
		print(f"Adding sense: {sense_xml_id}")
		for prop in sense['claims']:
			if prop in ["P9", "P10", "P11"]: # language style, location of sense use, field of use
				wd_prop = wd_mapping[prop]
				for claim in sense['claims'][prop]:
					claim_value = claim['mainsnak']['datavalue']['value']['id']
					if claim_value not in wd_mapping:
						continue
					wd_value = wd_mapping[claim_value]
					new_sense.claims.add(wdwbi.Item(prop_nr=wd_prop, value=wd_value, references=references),
										 action_if_exists=wdwbi.ActionIfExists.APPEND_OR_REPLACE)
					print(f"Claim added to sense: {wd_prop} > {wd_value}")
		for claim in entry_claims_for_senses:
			new_sense.claims.add(claim, action_if_exists=wdwbi.ActionIfExists.APPEND_OR_REPLACE)
			print(f"Claim from entry level added to sense: {claim}")
		wd_lexeme.senses.add(new_sense)

	switch_wbi_to("wdwbi")
	wd_lexeme.write(summary="Created new lexeme from Dicionário da Língua Portuguesa")
	print(f"Successfully written to https://www.wikidata.org/wiki/Lexeme:{wd_lexeme.id}")

	# write entry mapping to Wikibase
	nowtime = "+" + datetime.now().isoformat()[:11] + "00:00:00Z"
	references = ilwbi.References()
	reference = ilwbi.Reference()
	reference.add(ilwbi.Time(prop_nr="P17", time=nowtime, precision=11), action_if_exists=ilwbi.ActionIfExists.REPLACE_ALL)
	references.add(reference)
	qualifiers = [ilwbi.String(prop_nr="P14", value="new Wikidata lexeme created")]
	wb_lexeme.claims.add(ilwbi.ExternalID(prop_nr="P1", value=wd_lexeme.id, qualifiers=qualifiers, references=references), action_if_exists=ilwbi.ActionIfExists.REPLACE_ALL)

	# write sense mappings to Wikibase
	wd_senses = wd_lexeme.get_json()['senses']
	for wd_sense in wd_senses:
		wd_sense_id = wd_sense['id']
		if "P14752" in wd_sense['claims']:
			xml_id = wd_sense['claims']['P14752'][0]['mainsnak']['datavalue']['value']
			for wb_sense in wb_item['senses']:
				if wb_sense['claims']['P6'][0]['mainsnak']['datavalue']['value'] == xml_id:
					wb_sense_id = wb_sense['id']
					qualifiers = [ilwbi.String(prop_nr="P14", value="added to new Wikidata lexeme")]
					wb_lexeme.senses.get(id=wb_sense_id).claims.add(ilwbi.ExternalID(prop_nr="P1", value=wd_sense_id, qualifiers=qualifiers, references=references), action_if_exists=ilwbi.ActionIfExists.REPLACE_ALL)
	switch_wbi_to("ilwbi")
	wb_lexeme.write(summary="Add Wikidata mappings and Wikidata edit dates")
	print(f"Success writing new mappings to https://illlp.wikibase.cloud/entity/{wb_lexeme.id}")
	time.sleep(.12)

