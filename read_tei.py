import csv, sys
from xml.etree import cElementTree as ET, ElementTree
import re, json
import ilwbi

# get <usg> mappings
query = """PREFIX ilwb: <https://illlp.wikibase.cloud/entity/>
	PREFIX ildp: <https://illlp.wikibase.cloud/prop/direct/>
	
	select ?item ?classLabel ?usg_type ?property ?usg_value ?wikidata  where
	
	{ values ?class {ilwb:Q6 ilwb:Q7 ilwb:Q8} # domain, register, region
	  ?item ildp:P5 ?class; ildp:P7 ?usg_value. ?class ildp:P7 ?usg_type.
	  ?property ildp:P8 ?class.
	 optional {?item ildp:P1 ?wd. bind(iri(concat(str(wd:),?wd)) as ?wikidata)}
	
	SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
	} order by ?usg_type ?usg_value
	"""
usg_json = ilwbi.wbi_helpers.execute_sparql_query(query=query)['results']['bindings']
usg_codes = {'domain': {}, 'geographic': {}, 'socioCultural': {}}
for row in usg_json:
	usg_codes[row['usg_type']['value']][row['usg_value']['value']] = {'prop': row['property']['value'].replace("https://illlp.wikibase.cloud/entity/", ""), 'val': row['item']['value'].replace("https://illlp.wikibase.cloud/entity/", "")}
print(usg_codes)

grampgrp_codes = {}
with open("source/gramgrp.csv", "r") as csvfile:
	rows = csv.DictReader(csvfile, delimiter="\t")
	for row in rows:
		grampgrp_codes[row['value']] = row

pos_codes = {
	r"^n\.": "Q10", # noun
	r"^v\.": "Q11",# verb
	r"^adj\.": "Q12", # adjective
	r"^adv\.": "Q13" # adverb
			 }

source_file = "source/dic.xml"
error_report = "entry_id\tentry_status\terror\n"
lemma_attribs = {}
# load dictionary
tree = ET.ElementTree(file=source_file)
dictionary = tree.getroot()
print(f"\nSuccessfully loaded XML source: {source_file}")

# define URI pattern (from xml ID)
def make_uri(xml_id):
	return "https://dicionario.acad-ciencias.pt/id/" +  xml_id

def get_entry_info(entry, status=""):
	global error_report
	entry_id = entry.attrib['{http://www.w3.org/XML/1998/namespace}id']
	print(f"\nEntry ID: {entry_id}", end="")
	if entry_id.endswith(".xml"):
		print(f"Strange ID... goes to error report, and is skipped.")
		error_report += f"{entry_id}\t{status}\tEntry ID with '.xml' at the end\n"
		return None
	entry_object = {'xml_id': entry_id, 'uri': make_uri(entry_id), 'lemmas': []}
	for gramgrp in entry.findall('{http://www.tei-c.org/ns/1.0}gramGrp'):
		gramgrp_text = re.sub("\n"," ", gramgrp.text.strip())
		print(f" ({gramgrp_text})")
		for pos_code in pos_codes:
			if re.search(pos_code, gramgrp_text): # accepts only POS codes listed in pos_codes regular expressions
				wb_pos = pos_codes[pos_code]
				print(f"POS is {wb_pos}")
				entry_object['pos'] = wb_pos
		if "pos" not in entry_object:
			return None
		if gramgrp_text not in grampgrp_codes:
			input(f"Gramgrp code missing in mapping: {gramgrp_text}")
		else:
			codes = grampgrp_codes[gramgrp_text]
			if codes['m'] == "x":
				entry_object['masc'] = True
			if codes['f'] == "x":
				entry_object['fem'] = True
			if codes['pl'] == "x":
				entry_object['plurale_tantum'] = True

	for usg in entry.findall('{http://www.tei-c.org/ns/1.0}usg'):
		if 'usg' not in entry_object:
			entry_object['usg'] = []
		if usg.attrib['type'] not in usg_codes:
			continue
		if usg.attrib['type'] == 'geographic' and usg.text == "Region.":  # extra handling for "Portuguese Regionalism"
			print("Extra handling for Portuguese Regionalism")
			entry_object['usg'].append({'prop': "P10", 'val': "Q239"})  # language style (register) "regionalism"
			entry_object['usg'].append({'prop': "P11", 'val': "Q238"})  # location of sense use (geographic) "Portugal"
		elif usg.text not in usg_codes[usg.attrib['type']]:
			print(f"Unknown usg value of type {usg.attrib['type']}: {usg.text}")
			error_report += f"{result_entry['xml_id']}\t{entry_status}\tunknown <usg> of type '{usg.attrib['type']}': {usg.text}\n"
		else:
			entry_object['usg'].append({'prop': usg_codes[usg.attrib['type']][usg.text]['prop'],
			                            'val': usg_codes[usg.attrib['type']][usg.text]['val']})
			print(f"Added usg of type : {usg.attrib['type']}: {usg.text} > {usg_codes[usg.attrib['type']][usg.text]}")

	entry_object['lemmas'] = []
	formcount = 0
	for form in entry.findall('{http://www.tei-c.org/ns/1.0}form'):
		formcount += 1
		for orth in form.findall('{http://www.tei-c.org/ns/1.0}orth'):
			if not orth.text:
				print("Fatal error: No orth text.")
				error_report += f"{entry_id}\t{status}\tEmpty <orth>\n"
				continue
			if "render" in orth.attrib: # hidden in online DLP
				continue

			# exclude MWE
			lemma = orth.text.strip()
			if " " in lemma:
				return None

			if orth.attrib:
				attribs = orth.attrib
			else:
				attribs = {}
			print(attribs)
			print(f'Found lemma "{lemma}" with {len(attribs)} attributes.')
			for usg in orth.findall('{http://www.tei-c.org/ns/1.0}usg'):
				if "type" in usg.attrib:
					if usg.attrib['type'] == 'geographic' and usg.text == "Bras.":
						attribs["geographic"] = "pt-br"
			entry_object['lemmas'].append((lemma, attribs))
			for attrib, value in attribs.items():
				if attrib not in lemma_attribs:
					lemma_attribs[attrib] = [value]
				else:
					lemma_attribs[attrib].append(value)
	if formcount > 1:
		entry_object['multipleteiform'] = True
	if len(entry_object['lemmas']) == 0:
		print(f"Got no lemma... goes to error report, and is skipped.")
		error_report += f"{entry_id}\t{status}\tEntry ID with no valid <orth> content\n"
		return None

	return entry_object

def get_sense_info(sense):
	global error_report
	sense_id = sense.attrib['{http://www.w3.org/XML/1998/namespace}id']
	print(f"Found first-level sense with ID: {sense_id}")
	sense_object = {'xml_id': sense_id, 'uri': make_uri(sense_id), 'usg': []}
	# get usg
	for usg in sense.findall('{http://www.tei-c.org/ns/1.0}usg'):
		if usg.attrib['type'] not in usg_codes:
			continue
		if usg.attrib['type'] == 'geographic' and usg.text == "Region.": # extra handling for "Portuguese Regionalism"
			print("Extra handling for Portuguese Regionalism")
			sense_object['usg'].append({'prop': "P10", 'val': "Q239"}) # language style (register) "regionalism"
			sense_object['usg'].append({'prop': "P11", 'val': "Q238"}) # location of sense use (geographic) "Portugal"
		elif usg.text not in usg_codes[usg.attrib['type']]:
			print(f"Unknown usg value of type {usg.attrib['type']}: {usg.text}")
			error_report += f"{result_entry['xml_id']}\t{entry_status}\tunknown <usg> of type '{usg.attrib['type']}': {usg.text}\n"
		else:
			sense_object['usg'].append({'prop': usg_codes[usg.attrib['type']][usg.text]['prop'],
										'val': usg_codes[usg.attrib['type']][usg.text]['val']})
			print(f"Added usg of type : {usg.attrib['type']}: {usg.text} > {usg_codes[usg.attrib['type']][usg.text]}")

	# get definition
	sense_object['definition'] = None
	for definition in sense.findall('{http://www.tei-c.org/ns/1.0}def'):
		if definition.text:
			definition_text = ''.join(definition.itertext())
			if definition_text == "[...]":
				error_report += f"{result_entry['xml_id']}\t{entry_status}\t'[...]' <definition> in sense {sense_id}\n"
				continue
			definition_text = re.sub(r" +", " ", definition_text.replace("\n", " ").replace(" ,", ",").strip())
			sense_object['definition'] = definition_text
			print(f"Definition: {definition_text}")
		else:
			error_report += f"{result_entry['xml_id']}\t{entry_status}\tempty <definition> in sense {sense_id}\n"
	return sense_object

result_entries = []
subsenses = []
# iterate through entries
for entry in dictionary.findall('{http://www.tei-c.org/ns/1.0}entry'):
	# include only those with dacl annotation "imported"
	process = None
	for elem in entry.findall('{http://dacl.zbr.pt/annotations}meta'):
		if elem.attrib['status'] != "draft":
			process = True
			entry_status = elem.attrib['status']
			break
	if not process:
		continue
	# remove all <re> sections
	for parent in entry.findall('.//{http://www.tei-c.org/ns/1.0}re/..'):
		for element in parent.findall('{http://www.tei-c.org/ns/1.0}re'):
			parent.remove(element)

	# get entry level information
	result_entry = get_entry_info(entry, status=entry_status)
	if not result_entry:
		print("Entry POS not defined or MWE or info parsing otherwise unsuccessful")
		continue

	if entry_status == "":
		entry_status = "[empty]"
		error_report += f'{result_entry['xml_id']}\t[empty]\tEmpty "status" attribute\n'
	result_entry['status'] = entry_status

	#   iterate through all sense objects in the entry (that remain after removing <re>)
	result_entry['senses'] = []
	for sense in entry.findall('.//{http://www.tei-c.org/ns/1.0}sense'):
		if '{http://www.w3.org/XML/1998/namespace}id' not in sense.attrib:
			print("Fatal error: No sense ID")
			error_report += f"{result_entry['xml_id']}\t{entry_status}\t<sense> without xml_id\n"
			continue
		if len(sense.findall('{http://www.tei-c.org/ns/1.0}sense')) > 0:
			print(f"This sense contains subsenses. Recording and skipping.")
			subsenses.append(sense.attrib['{http://www.w3.org/XML/1998/namespace}id'])
			for subsense in sense.findall('{http://www.tei-c.org/ns/1.0}sense'):
				if '{http://www.w3.org/XML/1998/namespace}id' not in subsense.attrib:
					print("Fatal error: No sense ID")
					error_report += f"{result_entry['xml_id']}\t{entry_status}\t<sense> without xml_id\n"
					continue
				subsenses.append(subsense.attrib['{http://www.w3.org/XML/1998/namespace}id'])
			continue

		if sense.attrib['{http://www.w3.org/XML/1998/namespace}id'] in subsenses:
			print("This sense is a subsense. Skipping.")
			continue

		sense_object = get_sense_info(sense)
		if sense_object['definition']:
			result_entry['senses'].append(sense_object)

	if len(result_entry['senses']) > 0:
		result_entries.append(result_entry)

with open("result_entries.json", "w") as outfile:
	json.dump(result_entries, outfile, indent=2)

with open("error_report.csv", "w") as outfile:
	outfile.write(error_report)

print(f"Finished. Written {len(result_entries)} entries to result_entries.json")
with open("source/lemma_types.json", "w") as outfile:
	json.dump(lemma_attribs, outfile, indent=2)

print(f"\nSubsenses and their parents (excluded from results):\n\n{json.dumps(subsenses, indent=2)}")

