import csv
from xml.etree import cElementTree as ET
import re, json

pos_codes = {
    r"^n\.": "Q1084", # noun
    r"^v\.": "Q24905",# verb
    r"^adj\.": "Q34698", # adjective
    r"^adv\.": "Q380057" # adverb
             }

source_file = "source/dic.xml"

# load existing wikidata entries
with open('source/Wikidata_pt_lexemes.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    existing = {}
    for row in reader:
        if row['lemma'] not in existing:
            existing[row['lemma']] = [row]
        else:
            existing[row['lemma']].append(row)

# load dictionary
tree = ET.ElementTree(file=source_file)
dictionary = tree.getroot()
print(f"\nSuccessfully loaded XML source: {source_file}")

dlp_entries = {}
for entry in dictionary.findall('{http://www.tei-c.org/ns/1.0}entry'):
    entry_id = entry.attrib['{http://www.w3.org/XML/1998/namespace}id']
    print(f"\nEntry ID: {entry_id}", end="")
    process = True
    for elem in entry.findall('{http://dacl.zbr.pt/annotations}meta'):
        if elem.attrib['status'] == "draft":
            process = False
            break
    if not process:
        continue

    for gramgrp in entry.findall('{http://www.tei-c.org/ns/1.0}gramGrp'):
        gramgrp_text = re.sub("\n"," ", gramgrp.text)
        print(f" ({gramgrp_text})")
        for pos_code in pos_codes:
            if re.search(pos_code, gramgrp_text):
                wd_pos = pos_codes[pos_code]
                print(f"POS is {wd_pos}")

        for form in entry.findall('{http://www.tei-c.org/ns/1.0}form'):
            for orth in form.findall('{http://www.tei-c.org/ns/1.0}orth'):
                if not orth.text:
                    process = False
                    break
                lemma = orth.text.strip()
                print(f'Lemma is "{lemma}"')

                if lemma not in dlp_entries:
                    dlp_entries[lemma] = [{'pos': wd_pos, 'entry_id': entry_id}]
                else:
                    dlp_entries[lemma].append({'pos': wd_pos, 'entry_id': entry_id})

matching = []
wikidata_only_csv = "lemma\tposQid\tpos\twikidata_id\n"
wikidata_only = []

for lemma in existing.keys():
    print(f"now looking at lemma {lemma}")
    if lemma in dlp_entries:
        for existing_row in existing[lemma]:
            match = False
            for dlp_row in dlp_entries[lemma]:
                if existing_row['category'].replace("http://www.wikidata.org/entity/","") == dlp_row['pos']:
                    matching.append({'lemma': lemma, 'pos': dlp_row['pos'], 'wikidata_id': existing_row['lexemeId'], 'dlp_id': dlp_row['entry_id']})
                    match = True
            if not match:
                wikidata_only.append({'lemma': lemma, 'pos': existing_row['category'].replace("http://www.wikidata.org/entity/",""), 'wikidata_id': existing_row['lexemeId']})
                wikidata_only_csv += f"{lemma}\t{existing_row['category'].replace("http://www.wikidata.org/entity/","")}\t{existing_row['categoryLabel']}\t{existing_row['lexemeId']}\n"

with open("wikidata_only.json", "w") as outfile:
    json.dump(wikidata_only, outfile, indent=2)

with open("matching.json", "w") as outfile:
    json.dump(matching, outfile, indent=2)

with open("wikidata_only.csv", "w") as outfile:
    outfile.write(wikidata_only_csv)

