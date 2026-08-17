import csv, os, datetime
import json, re, sys, time, ilwbi

# open processed entries
with open("result_entries.json") as file:
    entries = json.load(file)
# date of the source file
# source_file_date = os.path.getmtime("source/dic.xml")
# source_file_date = datetime.datetime.fromtimestamp(source_file_date).isoformat()
# source_file_date = "+" + re.sub(r'T.*', 'T00:00:00Z', source_file_date)
source_file_date = "+2026-06-29T00:00:00Z"
print(source_file_date)

# open write log
with open("source/DLP-wikibase-senses.csv") as file:
    written_senses_csv = csv.DictReader(file, delimiter=',')
    written_senses = {}
    for row in written_senses_csv:
        written_senses[row['xml_id']] = row['sense']
with open("source/DLP-wikibase-entries.csv") as file:
    written_entries_csv = csv.DictReader(file, delimiter='\t')
    written_entries = {}
    for row in written_entries_csv:
        written_entries[row['xml_id']] = row['lexeme']

# iterate through entries
count = 0
for entry in entries:
    wb_lexeme = None
    count += 1

    print(f"[{count}/{len(entries)}] Now processing {entry['xml_id']}")
    # reference block to be attached to statements
    references = ilwbi.References()
    reference = ilwbi.Reference()
    reference.add(ilwbi.ExternalID(prop_nr="P6", value=entry['xml_id']))
    reference.add(ilwbi.Time(prop_nr="P12", time=source_file_date, precision=11))
    references.add(reference)
    gramgrp = False

    if entry['xml_id'] not in written_entries:
        input(f"Entry {entry['xml_id']} does not exist. Will create new. Press Enter.")

        # build lexeme
        wb_lexeme = ilwbi.wbi.lexeme.new(language="Q3", lexical_category=entry['pos'])
        wb_lexeme.lemmas.set(language="pt", value=entry['lemma'])
        wb_lexeme.claims.add(ilwbi.Item(prop_nr="P3", value="Q5", references=references))
        wb_lexeme.claims.add(ilwbi.ExternalID(prop_nr="P6", value=entry['xml_id'], references=references))
        wb_lexeme.claims.add(ilwbi.String(prop_nr="P13", value=entry['status'] if entry['status'] != "" else "[empty]",
                                       references=references))
        # build senses
        for sense in entry['senses']:
            if sense['xml_id'] not in written_senses:
                if not wb_lexeme:
                    wb_lexeme = ilwbi.wbi.lexeme.get(entity_id=written_entries[entry['xml_id']])
                new_sense = ilwbi.Sense()
                new_sense.claims.add(ilwbi.ExternalID(prop_nr= "P6", value=sense['xml_id'], references=references))
                new_sense.glosses.set(language="pt", value=sense['definition'])
                for usg_item in sense['usg']:
                    new_sense.claims.add(ilwbi.Item(prop_nr=usg_item['prop'], value=usg_item['val'], references=references))
                wb_lexeme.senses.add(new_sense)
                gramgrp = True
    else:
        wb_lexeme = ilwbi.wbi.lexeme.get(entity_id=written_entries[entry['xml_id']])


    if "masc" in entry:
        wb_lexeme.claims.add(ilwbi.Item(prop_nr="P15", value="Q17", references=references), action_if_exists=ilwbi.ActionIfExists.MERGE_REFS_OR_APPEND)
        gramgrp = True
    if "fem" in entry:
        wb_lexeme.claims.add(ilwbi.Item(prop_nr="P15", value="Q18", references=references), action_if_exists=ilwbi.ActionIfExists.MERGE_REFS_OR_APPEND)
        gramgrp = True
    if "plurale_tantum" in entry:
        wb_lexeme.claims.add(ilwbi.Item(prop_nr="P16", value="Q465", references=references), action_if_exists=ilwbi.ActionIfExists.MERGE_REFS_OR_APPEND)
        gramgrp = True



    if wb_lexeme and gramgrp:
        # write lexeme
        wb_lexeme.write()
        print(f"[{count}] Finished {entry['xml_id']}, written to https://illlp.wikibase.cloud/entity/{wb_lexeme.id}.")
        with open('written_senses.csv', 'a') as file:
            file.write(f"{entry['xml_id']}\t{wb_lexeme.id}\n")
        # wait (due to upload rate limit)
        time.sleep(.5)


