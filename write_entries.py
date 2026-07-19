import csv, os, datetime
import json, re, sys, time, ilwbi

# open processed entries
with open("result_entries.json") as file:
    entries = json.load(file)
# date of the source file
source_file_date = os.path.getmtime("source/dic.xml")
source_file_date = datetime.datetime.fromtimestamp(source_file_date).isoformat()
source_file_date = "+" + re.sub(r'T.*', 'T00:00:00Z', source_file_date)
print(source_file_date)
# open write log
with open("written_entries.csv") as file:
    written_entries_csv = csv.DictReader(file, delimiter='\t')
    written_entries = {}
    for row in written_entries_csv:
        written_entries[row['xml_id']] = row['wikibase_id']
# iterate through entries
count = 0
for entry in entries:
    count += 1
    if entry['xml_id'] in written_entries:
        print(f"Entry {entry['xml_id']} already written. Skipping.")
        continue
    # reference block to be attached to statements
    references = ilwbi.References()
    reference = ilwbi.Reference()
    reference.add(ilwbi.ExternalID(prop_nr="P6", value=entry['xml_id']))
    reference.add(ilwbi.Time(prop_nr="P12", time=source_file_date, precision=11))
    references.add(reference)
    # build lexeme
    lexeme = ilwbi.wbi.lexeme.new(language="Q3", lexical_category=entry['pos'])
    lexeme.lemmas.set(language="pt", value=entry['lemma'])
    lexeme.claims.add(ilwbi.Item(prop_nr="P3", value="Q5", references=references))
    lexeme.claims.add(ilwbi.ExternalID(prop_nr="P6", value=entry['xml_id'], references=references))
    lexeme.claims.add(ilwbi.String(prop_nr="P13", value=entry['status'], references=references))
    # build senses
    for sense in entry['senses']:
        new_sense = ilwbi.Sense()
        new_sense.claims.add(ilwbi.ExternalID(prop_nr= "P6", value=sense['xml_id'], references=references))
        new_sense.glosses.set(language="pt", value=sense['definition'])
        for usg_item in sense['usg']:
            new_sense.claims.add(ilwbi.Item(prop_nr=usg_item['prop'], value=usg_item['val'], references=references))
        lexeme.senses.add(new_sense)
    # write lexeme
    lexeme.write()
    print(f"[{count}] Finished {entry['xml_id']}, written to https://illlp.wikibase.cloud/entity/{lexeme.id}.")
    with open('written_entries.csv', 'a') as file:
        file.write(f"{entry['xml_id']}\t{lexeme.id}\n")
    # wait (due to upload rate limit)
    time.sleep(.34)


