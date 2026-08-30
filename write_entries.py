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
with open("source/tei_wb_map.csv") as file:
    existing_entities_csv = csv.DictReader(file, delimiter='\t')
    existing_entities = {}
    for row in existing_entities_csv:
        existing_entities[row['xml_id']] = row['entity']


# iterate through entries
count = 0
for entry in entries:

    wb_lexeme = None
    count += 1
    if len(entry['lemmas']) < 2:
        continue
    print(f"[{count}/{len(entries)}] Now processing {entry['xml_id']}")
    # reference block to be attached to statements
    references = ilwbi.References()
    reference = ilwbi.Reference()
    reference.add(ilwbi.ExternalID(prop_nr="P6", value=entry['xml_id']))
    reference.add(ilwbi.Time(prop_nr="P12", time=source_file_date, precision=11))
    references.add(reference)
    gramgrp = False

    if entry['xml_id'] not in existing_entities:
        input(f"Entry {entry['xml_id']} does not exist. Will create new. Press Enter.")

        # build lexeme
        wb_lexeme = ilwbi.wbi.lexeme.new(language="Q3", lexical_category=entry['pos'])
    else:
        wb_lexeme = ilwbi.wbi.lexeme.get(entity_id=existing_entities[entry['xml_id']])
        print(f"Got data for https://illlp.wikibase.cloud/entity/{wb_lexeme.id}.")
        time.sleep(.1)

    # lemmas
    lemdict = {"pt": None, "pt-br": None, "pt-colb1945": None, "pt-x-Q59342809": None}

    for lemtuple in entry['lemmas']:
        lemqualis = []
        print(lemtuple)
        lemma = lemtuple[0]
        attribs = lemtuple[1]
        if "geographic" in attribs:
            if attribs["geographic"] == "pt-br": # Brazil lemma
                if not lemdict['pt-br']:
                    lemdict['pt-br'] = lemma
                lemqualis.append(ilwbi.Item(prop_nr="P11", value="Q204"))
        elif "ao" in attribs:
            if not lemdict['pt-colb1945']: # old orthography
                lemdict['pt-colb1945'] = lemma
            lemqualis.append(ilwbi.Item(prop_nr="P16", value="Q23"))
        elif "fem" in attribs:
            lemqualis.append(ilwbi.String(prop_nr="P20", value=attribs["fem"].strip()))
            if not lemdict['pt']:
                lemdict['pt'] = lemma
            elif not lemdict["pt-x-Q59342809"]:
                lemdict['pt-x-Q59342809'] = lemma
        elif "foreign" in attribs:
            lemqualis.append(ilwbi.Item(prop_nr="P16", value="Q24"))
            if not lemdict['pt']:
                lemdict['pt'] = lemma
            elif not lemdict["pt-x-Q59342809"]:
                lemdict['pt-x-Q59342809'] = lemma
        else:
            if not lemdict['pt']:
                lemdict['pt'] = lemma
            elif not lemdict["pt-x-Q59342809"]:
                lemdict['pt-x-Q59342809'] = lemma
        # as P19 claim always
        wb_lexeme.claims.add(ilwbi.String(prop_nr="P19", value=lemma, qualifiers=lemqualis, references=references), action_if_exists=ilwbi.ActionIfExists.MERGE_REFS_OR_APPEND)
        # as wikibase:lemma only one per language code
    lemmajson = {}
    for lang, value in lemdict.items():
        if value:
            lemmajson[lang] = {"language": lang, "value": value}

    existing_lemmas = wb_lexeme.lemmas.get_json()
    for lang in existing_lemmas:
        if lang not in lemmajson:
            lemmajson[lang] = {"language": lang, "value": "[del]"}
        elif not lemmajson[lang]:
            lemmajson[lang]["value"] = "[del]"

    wb_lexeme.lemmas.from_json(lemmajson)

    wb_lexeme.claims.add(ilwbi.Item(prop_nr="P3", value="Q5", references=references))
    wb_lexeme.claims.add(ilwbi.ExternalID(prop_nr="P6", value=entry['xml_id'], references=references))
    wb_lexeme.claims.add(ilwbi.String(prop_nr="P13", value=entry['status'] if entry['status'] != "" else "[empty]",
                                   references=references))
    # build senses
    # for sense in entry['senses']:
    #     if sense['xml_id'] not in existing_entities:
    #         if not wb_lexeme:
    #             wb_lexeme = ilwbi.wbi.lexeme.get(entity_id=existing_entities[entry['xml_id']])
    #         new_sense = ilwbi.Sense()
    #         new_sense.claims.add(ilwbi.ExternalID(prop_nr= "P6", value=sense['xml_id'], references=references), action_if_exists=ilwbi.ActionIfExists.MERGE_REFS_OR_APPEND)
    #         new_sense.glosses.set(language="pt", value=sense['definition'])
    #         for usg_item in sense['usg']:
    #             new_sense.claims.add(ilwbi.Item(prop_nr=usg_item['prop'], value=usg_item['val'], references=references), action_if_exists=ilwbi.ActionIfExists.MERGE_REFS_OR_APPEND)
    #         input(f"Adding new sense to this lexeme.")
    #         wb_lexeme.senses.add(new_sense)
    #         gramgrp = True




    if "masc" in entry:
        wb_lexeme.claims.add(ilwbi.Item(prop_nr="P15", value="Q17", references=references), action_if_exists=ilwbi.ActionIfExists.MERGE_REFS_OR_APPEND)
        gramgrp = True
    if "fem" in entry:
        wb_lexeme.claims.add(ilwbi.Item(prop_nr="P15", value="Q18", references=references), action_if_exists=ilwbi.ActionIfExists.MERGE_REFS_OR_APPEND)
        gramgrp = True
    if "plurale_tantum" in entry:
        wb_lexeme.claims.add(ilwbi.Item(prop_nr="P16", value="Q465", references=references), action_if_exists=ilwbi.ActionIfExists.MERGE_REFS_OR_APPEND)
        gramgrp = True

    if "usg" in entry:
        for usg_item in entry['usg']:
            wb_lexeme.claims.add(ilwbi.Item(prop_nr=usg_item['prop'], value=usg_item['val'], references=references), action_if_exists=ilwbi.ActionIfExists.MERGE_REFS_OR_APPEND)
            print(f"Adding new usg to this lexeme.")



    if wb_lexeme:
        # write lexeme
        # print(json.dumps(wb_lexeme.get_json(), indent=2))
        wb_lexeme.write()
        print(f"[{count}] Finished {entry['xml_id']}, written to https://illlp.wikibase.cloud/entity/{wb_lexeme.id}.")
        # wait (due to upload rate limit)
        time.sleep(.21)


