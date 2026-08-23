import csv
import json, sys, time, requests, re

headers = {"User-Agent": "User:DL2204 python requests"}

# load Wikibase dictionary: All Wikidata-aligned entries without any aligned sense
url = "https://illlp.wikibase.cloud/query/sparql?format=json&query=PREFIX%20ilwb%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fentity%2F%3E%0APREFIX%20ildp%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fdirect%2F%3E%0APREFIX%20ilp%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2F%3E%0APREFIX%20ilps%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fstatement%2F%3E%0APREFIX%20ilpq%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fqualifier%2F%3E%0APREFIX%20ilpr%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Freference%2F%3E%0APREFIX%20ilno%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fnovalue%2F%3E%0A%0Aselect%20%3Flexeme%20(count(%3Fsense)%20as%20%3Fsenses)%20%3Fwd_lexeme%20where%0A%0A%7B%20%3Flexeme%20dct%3Alanguage%20ilwb%3AQ3%3B%20ilp%3AP1%20%5Bilps%3AP1%20%3Fwd%5D.%0A%20%20%3Flexeme%20ontolex%3Asense%20%3Fsense.%20filter%20not%20exists%20%7B%3Fsense%20ildp%3AP1%20%5B%5D%7D.%0A%20bind(iri(concat(str(wd%3A)%2C%3Fwd))%20as%20%3Fwd_lexeme)%0A%20%20%20%0A%20%0A%7D%20group%20by%20%3Flexeme%20%3Fsenses%20%3Fwd_lexeme"
wb_r = requests.get(headers=headers, url=url)
print(wb_r)
result = wb_r.json()['results']['bindings']
print(f"Got {len(result)} aligned lexemes with some unaligned sense from DLP Wikibase.")
wikibase = {}
for row in result:
    wikibase[row['lexeme']['value'].replace("https://illlp.wikibase.cloud/entity/","")] = row['wd_lexeme']['value'].replace("http://www.wikidata.org/entity/","")

# load existing wikidata entries that have some unaligned sense
url = "https://query.wikidata.org/sparql?format=json&query=select%20distinct%20%3Flexeme%20where%0A%20%20%20%20%20%7B%20%3Flexeme%20dct%3Alanguage%20wd%3AQ5146.%0A%20%20%20%20%20%20%20%0A%20%20%20%20%20%20%20%3Flexeme%20ontolex%3Asense%20%3Fsense.%0A%20%20%20%20%20%20%20filter%20not%20exists%20%7B%3Fsense%20wdt%3AP14752%20%5B%5D.%7D%0A%20%20%20%20%20%20%20values%20%3Fpos%20%7Bwd%3AQ1084%20wd%3AQ24905%20wd%3AQ34698%20wd%3AQ380057%7D%0A%20%20%20%20%20%20%3Flexeme%20wikibase%3AlexicalCategory%20%3Fpos.%0A%20%20%20%20%20%7D%20%0A%20%20"
wb_r = requests.get(headers=headers, url=url)
print(wb_r)
result = wb_r.json()['results']['bindings']
print(f"Got {len(result)} lexemes with all unaligned senses from Wikidata.")
wikidata = []
for row in result:
    wikidata.append(row['lexeme']['value'].replace("http://www.wikidata.org/entity/",""))

with open("source/manual-sense-matching.txt") as file:
    done_items = []
    for line in file.readlines():
        done_items.append(re.search(r'P1\t"(L\d+)', line).group(1))
    print(done_items)


count = 0
for wb_id, wd_id in wikibase.items():
    count += 1
    print(f"\n[{count}/{len(wikibase)}] Now processing: https://illlp.wikibase.cloud/entity/{wb_id}.")
    if wd_id in done_items:
        print("Done. skipping item.")
        continue
    # get wikidata item
    headers = {"User-Agent": "User:DL2204 python requests"}
    wd_item_r = requests.get(headers=headers, url=f"https://www.wikidata.org/wiki/Special:EntityData/{wd_id}.json")
    wd_item = wd_item_r.json()['entities'][wd_id]
    print(f"Lemma is: ** {wd_item['lemmas']['pt']['value']} **")
    print(f"https://www.wikidata.org/wiki/Lexeme:{wd_id} has {len(wd_item['senses'])} senses:")
    wd_sense_count = 0
    sense_selection = {}
    if len(wd_item['senses']) == 0:
        print("No senses found. Mapping thus OK.")
        done_items.append(wd_id)
        continue
    process = True
    for sense in wd_item['senses']:
        wd_sense_count += 1
        if "P14752" in sense['claims']:
            print("This Wikidata lexeme has aligned senses. Skipping.")
            process = False
            break
        print(f"Wikidata [{wd_sense_count}] * " + str(sense))
        sense_selection[str(wd_sense_count)] = sense['id']
    if not process:
        continue

    # get wikibase item
    wb_item_r = requests.get(headers=headers,
                             url=f"https://illlp.wikibase.cloud/wiki/Special:EntityData/{wb_id}.json")
    wb_item = wb_item_r.json()['entities'][wb_id]
    print(f"https://illlp.wikibase.cloud/wiki/Lexeme:{wb_id} has {len(wb_item['senses'])} senses:")
    selection = {}
    wb_sense_count = 0
    for sense in wb_item['senses']:
        wb_sense_count += 1
        print(f"Wikibase {wb_sense_count} * " + str(sense))
        selection[str(wb_sense_count)] = sense['id']

    for sense in sense_selection:
        select = input(f"For Wikidata sense [{sense}]: Enter matching wikibase sense number, 0=no match\n")
        if select == "0":
            with open('source/manual-sense-matching.txt', 'a') as file:
                file.write(f'No match\tP1\t"{sense_selection[sense]}"\tP14\t"no match"\n')
                done_items.append(wd_id)
                continue
        # elif select == "x":
        #     with open('source/manual-sense-matching.txt', 'a') as file:
        #         file.write(f"https://www.wikidata.org/wiki/Lexeme:{sense_selection[sense]}\tsplit candidate (multiple matches)\n")
        #         continue
        elif select not in selection:
            print("Invalid input, skipping item.")
            continue
        print(f"Selected Sense ID: {selection[select]}")


        with open('source/manual-sense-matching.csv', 'a') as file:
            file.write(f'{selection[select]}\tP1\t"{sense_selection[sense]}"\tP14\t"manually disambiguated"\n')

        print(f"Successfully stored mapping for https://illlp.wikibase.cloud/wiki/Lexeme:{wb_id}")


