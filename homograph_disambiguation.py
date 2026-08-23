import json, sys, time, requests, ilwbi, re

with open('source/multiple-match.json') as json_file:
    data = json.load(json_file)

with open("source/manual-matching.txt") as file:
    done_items = []
    for line in file.readlines():
        done_items.append(re.search(r'Lexeme:(L\d+)', line).group(1))


for item in data:
    print(f"\nNow processing: {item['lemma']} ({item['pos']}), {item['matches']} matches.")
    if item['wikidata'] in done_items:
        print("Done. skipping item.")
        continue
    # get wikidata item
    headers = {"User-Agent": "User:DL2204 python requests"}
    wd_item_r = requests.get(headers=headers, url=f"https://www.wikidata.org/wiki/Special:EntityData/{item['wikidata']}.json")
    wd_item = wd_item_r.json()['entities'][item['wikidata']]
    print(f"https://www.wikidata.org/wiki/Lexeme:{item['wikidata']} has {len(wd_item['senses'])} senses:")
    for sense in wd_item['senses']:
        print("* " + str(sense))
    # get wikibase items
    lidcount = 0
    selection = {}
    for lid in item['wikibase']:
        lidcount += 1
        wb_item_r = requests.get(headers=headers,
                                 url=f"https://illlp.wikibase.cloud/wiki/Special:EntityData/{lid}.json")
        wb_item = wb_item_r.json()['entities'][lid]
        print(f"[{lidcount}] https://illlp.wikibase.cloud/wiki/Lexeme:{lid} has {len(wb_item['senses'])} senses:")
        for sense in wb_item['senses']:
            print("* " + str(sense))
        selection[str(lidcount)] = lid

    select = input("Enter matching lexeme number, 0=no match, x=split candidate (multiple matches)\n")
    if select == "0":
        with open('source/manual-matching.txt', 'a') as file:
            file.write(f"https://www.wikidata.org/wiki/Lexeme:{item['wikidata']}\tno match\n")
            continue
    elif select == "x":
        with open('source/manual-matching.txt', 'a') as file:
            file.write(f"https://www.wikidata.org/wiki/Lexeme:{item['wikidata']}\tsplit candidate (multiple matches)\n")
            continue
    elif select not in selection:
        print("Invalid input, skipping item.")
        continue
    print(f"Selected LID: {selection[select]}")

    wb_item = ilwbi.wbi.lexeme.get(entity_id=selection[select])
    wb_item.claims.add(ilwbi.ExternalID(prop_nr="P1", value=item['wikidata'], qualifiers=[ilwbi.String(prop_nr="P14", value="manual homograph disambiguation")]), action_if_exists=ilwbi.ActionIfExists.REPLACE_ALL)
    wb_item.write()
    with open('source/manual-matching.txt', 'a') as file:
        file.write(f"https://www.wikidata.org/wiki/Lexeme:{item['wikidata']}\tmanually disambiguated ({item['matches']} candidates)\n")

    print(f"Successfully written to https://illlp.wikibase.cloud/wiki/Lexeme:{wb_item.id}")
    done_items.append(item['wikidata'])


