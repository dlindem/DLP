import csv
import json, ilwbi

# get entries
print("Getting entries...")
query = """PREFIX ilwb: <https://illlp.wikibase.cloud/entity/>
PREFIX ildp: <https://illlp.wikibase.cloud/prop/direct/>
PREFIX ilp: <https://illlp.wikibase.cloud/prop/>
PREFIX ilps: <https://illlp.wikibase.cloud/prop/statement/>
PREFIX ilpq: <https://illlp.wikibase.cloud/prop/qualifier/>
PREFIX ilpr: <https://illlp.wikibase.cloud/prop/reference/>
PREFIX ilno: <https://illlp.wikibase.cloud/prop/novalue/>

select ?entity ?xml_id ?source_date  where

{ ?entity dct:language ilwb:Q3; ilp:P6 [ilps:P6 ?xml_id; prov:wasDerivedFrom [ilpr:P12 ?source_date]].
  }
  """
results = ilwbi.wbi_helpers.execute_sparql_query(query)
bindings = results['results']['bindings']

with open("source/tei_wb_map.csv", "w") as csvfile:
    csvfile.write("entity\txml_id\tsource_date\n")
with open("source/tei_wb_map.csv", "a") as csvfile:
    for binding in bindings:
        csvfile.write(f"{binding['entity']['value'].replace("https://illlp.wikibase.cloud/entity/","")}\t{binding['xml_id']['value']}\t{binding['source_date']['value']}\n")
print("Successfully stored entry mapping to tei_wb_map.csv")

# get senses
print("Getting senses...")
query = """PREFIX ilwb: <https://illlp.wikibase.cloud/entity/>
PREFIX ildp: <https://illlp.wikibase.cloud/prop/direct/>
PREFIX ilp: <https://illlp.wikibase.cloud/prop/>
PREFIX ilps: <https://illlp.wikibase.cloud/prop/statement/>
PREFIX ilpq: <https://illlp.wikibase.cloud/prop/qualifier/>
PREFIX ilpr: <https://illlp.wikibase.cloud/prop/reference/>
PREFIX ilno: <https://illlp.wikibase.cloud/prop/novalue/>

select ?entity ?xml_id ?source_date  where

{ ?lexeme  dct:language ilwb:Q3; ontolex:sense ?entity. ?entity ilp:P6 [ilps:P6 ?xml_id; prov:wasDerivedFrom [ilpr:P12 ?source_date]].
  }
  """
results = ilwbi.wbi_helpers.execute_sparql_query(query)
bindings = results['results']['bindings']

with open("source/tei_wb_map.csv", "a") as csvfile:
    csvfile.write("entity\txml_id\tsource_date\n")
    for binding in bindings:
        csvfile.write(f"{binding['entity']['value'].replace("https://illlp.wikibase.cloud/entity/","")}\t{binding['xml_id']['value']}\t{binding['source_date']['value']}\n")
print("Successfully stored sense mapping to tei_wb_map.csv")
