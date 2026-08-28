import csv, sys, time, re
from datetime import datetime

import ilwbi

import wdwbi  # Wikidata via WikibaseIntegrator
import mwclient  # Wikibase via mwclient
from config_private import wb_bot_user, wb_bot_pwd
import requests, json
from wikibaseintegrator.wbi_enums import ActionIfExists

headers = {"User-Agent": "User:DL2204 python requests"}

site = mwclient.Site("illlp.wikibase.cloud")

def get_token():
    global site
    while True:
        try:
            login = site.login(username=wb_bot_user, password=wb_bot_pwd)
            break
        except Exception as ex:
            print('Wikibase login via mwclient raised error: ' + str(ex))
            time.sleep(60)
    # get token
    csrfquery = site.api('query', meta='tokens')
    token = csrfquery['query']['tokens']['csrftoken']
    print(f"Got fresh CSRF token for Wikibase.")
    return token
token = get_token()

def write_mapping(wb_entity, wd_entity, entity_type):
    global token



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

count = 0
for wb_lexeme_id, wb_data in wb_lexemes.items():
    count += 1
    if count > 3: # to be removed for production
        sys.exit()
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
    wb_item_r = requests.get(headers=headers,
                             url=f"https://illlp.wikibase.cloud/wiki/Special:EntityData/{wb_lexeme_id}.json")
    wb_item = wb_item_r.json()['entities'][wb_lexeme_id]
    entry_xml_id = wb_item['claims']['P6'][0]['mainsnak']['datavalue']['value']
    wb_lexeme_source_date = wb_item['claims']['P6'][0]['references'][0]['snaks']['P12'][0]['datavalue']['value']['time']
    print(
        f"Got data for https://illlp.wikibase.cloud/wiki/Lexeme:{wb_lexeme_id}, with {len(wb_item['senses'])} senses.")

    # get wd lexeme
    wd_lexeme_id = wb_data['wd_lexeme']['value'].replace("http://www.wikidata.org/entity/", "")
    wd_lexeme = wdwbi.wbi.lexeme.get(entity_id=wd_lexeme_id)

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
            print(f"Sense {wb_sense['id']} is already aligned to {alignments[wb_sense['id']]}...")
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
                new_sense.claims.add(wdwbi.Item(prop_nr=wd_prop, value=wd_value, references=references), action_if_exists=ilwbi.ActionIfExists.APPEND_OR_REPLACE)

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
        print(f"Sense {wb_sense['id']} has been added as new sense to the lexeme.")
    wd_lexeme.write()
    print(f"Successfully written to https://www.wikidata.org/wiki/Lexeme:{wd_lexeme.id}")

    # write sense mappings to Wikibase
    wd_senses = wd_lexeme.get_json()['senses']
    for wd_sense in wd_senses:
        wd_sense_id = wd_sense['id']
        if "P14752" in wd_sense['claims']:
            xml_id = wd_sense['claims']['P14752'][0]['mainsnak']['datavalue']['value']
            for wb_sense in wb_item['senses']:
                wb_sense_id = wb_sense['id']
                if wb_sense['claims']['P6'][0]['mainsnak']['datavalue']['value'] == xml_id and wb_sense_id not in alignments:
                    # write mapping information to Wikibase
                    claim_id = None
                    while (not claim_id):
                        try:
                            request = site.post('wbcreateclaim', token=token, entity=wb_sense_id, property="P1",
                                                snaktype="value",
                                                value=f'"{wd_sense_id}"',
                                                bot=1, summary=f"Wikidata sense created from scratch.")
                            if request['success'] == 1:
                                done = True
                                claim_id = request['claim']['id']
                                print(f"Wikibase: Created claim {wb_sense_id} - P1 - {wd_sense_id}...", end=" ")
                            time.sleep(.34)
                        except Exception as ex:
                            if 'Invalid CSRF token.' in str(ex):
                                print('Wait a sec. Must get a new CSRF token...')
                                token = get_token()
                            else:
                                print('Claim creation failed, will try again...\n' + str(ex))
                                time.sleep(4)

                    guidfix = re.compile(r'^(L\d+\-S\d+)\-')  # senses
                    claim_id = re.sub(guidfix, r'\1$', claim_id)
                    guidfix = re.compile(r'^(L\d+)\-([^\-$]{8})')  # lexemes
                    claim_id = re.sub(guidfix, r'\1$\2', claim_id)
                    # provenance comment qualifier
                    comment = "added to existing Wikidata lexeme"
                    while True:
                        try:
                            setqualifier = site.post('wbsetqualifier', token=token, claim=claim_id, property="P14",
                                                     snaktype="value",
                                                     value=f'"{comment}"', bot=1)
                            if setqualifier['success'] == 1:
                                print('Qualifier set successfully (' + comment + ').', end=" ")
                                time.sleep(.34)
                                break
                        except Exception as ex:
                            if 'Invalid CSRF token.' in str(ex):
                                print('Wait a sec. Must get a new CSRF token...')
                                time.sleep(10)
                                token = get_token()
                            else:
                                print(str(ex))
                                print('Qualifier set failed, will try again...')
                            time.sleep(2)
                    # wikidata edit time reference
                    nowtime = "+" + datetime.now().isoformat()[:11] + "00:00:00Z"
                    refsnaks = json.dumps(
                        {"P17": [{"snaktype": "value", "property": "P17",
                                  "datavalue": {"type": "time", "value": {"time": nowtime, "timezone": 0,
                                                                          "before": 0,
                                                                          "after": 0, "precision": 11,
                                                                          "calendarmodel": "http://www.wikidata.org/entity/Q1985727"}}}]})
                    while True:
                        try:
                            setref = site.post('wbsetreference', token=token, statement=claim_id, index=0,
                                               snaks=refsnaks, bot=1)
                            if setref['success'] == 1:
                                print(f'Time reference {nowtime} successfully set.')
                                time.sleep(.34)
                                break
                        except Exception as ex:
                            if 'Invalid CSRF token.' in str(ex):
                                print('Wait a sec. Must get a new CSRF token...')
                                time.sleep(10)
                                token = get_token()
                            else:
                                print(str(ex))
                                print('Reference set failed, will try again...')
                            print(str(ex))
                            time.sleep(5)
