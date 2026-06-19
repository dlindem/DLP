from xml.etree import cElementTree as ET
import re, json

pos_codes = {r"^n\.": "Q1084" # noun
             }

gender_codes = {r"m\.$": "Q499327" # masculine
                }

domain_codes = {"Zool.": "Q431", # Zoology
                "Desp.": "Q349", # Sport
                "Tip.": "Q159964" # Tipography
                }

source_file = "source/cavalo_1-c9654.xml"

# load dictionary
tree = ET.ElementTree(file=source_file)
dictionary = tree.getroot()
print(f"\nSuccessfully loaded XML source: {source_file}")
for elem in dictionary.iter():
    print(str(elem))
    print(str(elem.attrib))

# define URI pattern (from xml ID)
def make_uri(xml_id):
    return "https://dicionario.acad-ciencias.pt/id/" + re.sub(r"^DLP-", "", xml_id)

def get_entry_info(entry):
    entry_id = entry.attrib['{http://www.w3.org/XML/1998/namespace}id']
    print(f"\nEntry ID: {entry_id}", end="")
    entry_object = {'xml_id': entry_id, 'uri': make_uri(entry_id)}
    for gramgrp in entry.findall('{http://www.tei-c.org/ns/1.0}gramGrp'):
        gramgrp_text = gramgrp.text
        print(f" ({gramgrp_text})")
        for pos_code in pos_codes:
            if re.search(pos_code, gramgrp_text):
                wd_pos = pos_codes[pos_code]
                print(f"POS is {wd_pos}")
                entry_object['pos'] = wd_pos
                if wd_pos == "Q1084": # noun entry
                    # get gender
                    for gender_code in gender_codes:
                        if re.search(gender_code, gramgrp_text):
                            wd_gender = gender_codes[gender_code]
                            print(f"Gender is {wd_gender}")
                            entry_object['gender'] = wd_gender

        for form in entry.findall('{http://www.tei-c.org/ns/1.0}form'):
            for orth in form.findall('{http://www.tei-c.org/ns/1.0}orth'):
                lemma = orth.text
                print(f'Lemma is "{lemma}"')
                entry_object['lemma'] = lemma
                # exclude MWE?
    return entry_object

result_entries = []
# iterate through entries
for entry in dictionary.findall('{http://www.tei-c.org/ns/1.0}entry'):
    # get entry level information
    result_entry = get_entry_info(entry)
    if not result_entry:
        print("Entry POS not defined or info parsing otherwise unsuccessful")
        continue

    # iterate through first-level senses
    result_entry['senses'] = []
    for sense in entry.findall('{http://www.tei-c.org/ns/1.0}sense'):
        sense_id = sense.attrib['{http://www.w3.org/XML/1998/namespace}id']
        print(f"Found first-level sense with ID: {sense_id}")
        sense_object = {'xml_id': sense_id, 'uri': make_uri(sense_id)}
        # get usg
        for usg in sense.findall('{http://www.tei-c.org/ns/1.0}usg'):
            if usg.attrib['type'] == "domain":
                if usg.text not in domain_codes:
                    sense_object['domain'] = f"* unknown domain '{usg.text}' *"
                    print(f"Unknown domain: {usg.text}")
                else:
                    sense_object['domain'] = domain_codes[usg.text]
                    print(f"Domain: {sense_object['domain']}")
            elif usg.attrib['type'] == "socioCultural":
                pass # TODO: register codes

        # get definition
        for definition in sense.findall('{http://www.tei-c.org/ns/1.0}def'):
            sense_object['definition'] = re.sub(r" +", " ", definition.text.replace("\n", " ").strip())
            print(f"Definition: {sense_object['definition']}")
        result_entry['senses'].append(sense_object)

    result_entries.append(result_entry)

with open("result_entries.json", "w") as outfile:
    json.dump(result_entries, outfile, indent=2)

