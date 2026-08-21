import csv, sys, requests
from xml.etree import cElementTree as ET
import re, json

headers = {"User-Agent": "User:DL2204 python requests"}

pos_codes = {
	"Q10": "Q1084", # noun
	"Q11": "Q24905",# verb
	"Q12": "Q34698", # adjective
	"Q13": "Q380057" # adverb
			 }

# load existing wikidata entries that are not aligned to DLP
url = "https://query.wikidata.org/sparql?format=json&query=select%20%3Flemma%20(lang(%3Flemma)%20as%20%3Flemmalang)%20%3Fpos%20%3Flexeme%20where%0A%20%20%20%20%20%7B%20%3Flexeme%20dct%3Alanguage%20wd%3AQ5146.%0A%20%20%20%20%20%20%20filter%20not%20exists%20%7B%3Flexeme%20wdt%3AP14752%20%5B%5D.%7D%0A%20%20%20%20%20%20%20values%20%3Fpos%20%7Bwd%3AQ1084%20wd%3AQ24905%20wd%3AQ34698%20wd%3AQ380057%7D%0A%20%20%20%20%20%20%3Flexeme%20wikibase%3AlexicalCategory%20%3Fpos%3B%20wikibase%3Alemma%20%3Flemma.%0A%20%20%20%20%20%7D%20%0A%20%20"
wb_r = requests.get(headers=headers, url=url)
print(wb_r)
result = wb_r.json()['results']['bindings']
print(f"Got {len(result)} unaligned lemma from Wikidata.")
wikidata = {}
for row in result:
	lemdata = {"lexeme": row['lexeme']['value'].replace("http://www.wikidata.org/entity/", ""),
	   "pos": row['pos']['value'].replace("http://www.wikidata.org/entity/", "")}
	if row['lemma']['value'] not in wikidata:
		wikidata[row['lemma']['value']] = [lemdata]
	else:
		wikidata[row['lemma']['value']].append(lemdata)

# load Wikibase dictionary
url = "https://illlp.wikibase.cloud/query/sparql?format=json&query=PREFIX%20ilwb%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fentity%2F%3E%0APREFIX%20ildp%3A%20%3Chttps%3A%2F%2Filllp.wikibase.cloud%2Fprop%2Fdirect%2F%3E%0A%0Aselect%20%3Flemma%20(lang(%3Flemma)%20as%20%3Flemmalang)%20%3Flexeme%20%3Fpos%20%3Fwd_pos%20where%0A%7B%0A%20%20%3Flexeme%20dct%3Alanguage%20ilwb%3AQ3%3B%20wikibase%3Alemma%20%3Flemma%3B%20wikibase%3AlexicalCategory%20%3Fpos.%0A%20%20%3Fpos%20ildp%3AP1%20%3Fwd_pos.%0A%20%0A%20filter%20not%20exists%20%7B%3Flexeme%20ildp%3AP1%20%3Fwd_alignment.%7D%0A%20%0A%20%7D%20"
wb_r = requests.get(headers=headers, url=url)
print(wb_r)
result = wb_r.json()['results']['bindings']
print(f"Got {len(result)} unaligned lemma from DLP Wikibase.")
dlp = {}
homographs = {}
for row in result:
	lemma = row['lemma']['value']
	pos = row['pos']['value'].replace("https://illlp.wikibase.cloud/entity/","")
	lexeme = row['lexeme']['value'].replace("https://illlp.wikibase.cloud/entity/","")
	if lemma not in dlp:
		dlp[lemma] = {pos: [lexeme]}
	elif pos not in dlp[lemma]:
		dlp[lemma][pos] = [lexeme]
	else:
		dlp[lemma][pos].append(lexeme)
		# homographs[row['lemma']] = {row['pos_item']: dlp[row['lemma']][row['pos_item']]}

# with open('source/homographs.json', 'w') as outfile:
# 	json.dump(homographs, outfile, indent=2)


one_match = []
multiple_match = []

for wd_lemma, data in wikidata.items():
	print(f"now looking at lemma {wd_lemma}, with {len(data)} entries.")

	for entry in data:
		matches = []
		wd_pos = entry['pos']
		for dlp_lemma in dlp:
			if dlp_lemma == wd_lemma:
				for wb_pos in dlp[dlp_lemma]:
					if pos_codes[wb_pos] == wd_pos:
						matches = dlp[dlp_lemma][wb_pos]


		if len(matches) == 1:
			# print(f"{lemma} has one match")
			one_match.append({"wikibase": matches[0], "wikidata": entry['lexeme'], "lemma": wd_lemma, "pos": wd_pos})

		elif len(matches) > 1:
			# print(f"{lemma} has multiple matches")
			multiple_match.append(
				{"matches": len(matches), "wikibase": matches, "wikidata": entry['lexeme'], "lemma": wd_lemma, "pos": wd_pos})


with open('source/one-match.json', 'w') as outfile:
	json.dump(one_match, outfile, indent=2)

df = open('source/one-match.csv', 'w', newline='')
cw = csv.writer(df)

c = 0
for data in one_match:
	if c == 0:
		header = data.keys()
		cw.writerow(header)
		c += 1
	cw.writerow(data.values())

df.close()


with open('source/multiple-match.json', 'w') as outfile:
	json.dump(multiple_match, outfile, indent=2)






