from xml.etree import cElementTree as ET
import re, json

source_file = "source/dic.xml"
gramGrp_values = {}

# load dictionary
tree = ET.ElementTree(file=source_file)
dictionary = tree.getroot()
print(f"\nSuccessfully loaded XML source: {source_file}")
for entry in dictionary.findall("{http://www.tei-c.org/ns/1.0}entry"):
    process = False
    for elem in entry.findall('{http://dacl.zbr.pt/annotations}meta'):
        if elem.attrib['status'] == "imported":
            process = True
            break
    if not process:
        continue
    for elem in entry.findall('{http://www.tei-c.org/ns/1.0}gramGrp'):
        if elem.text not in gramGrp_values:
            gramGrp_values[elem.text] = 1
        else:
            gramGrp_values[elem.text] += 1

with open("gramGrp_values.json", "w") as outfile:
    json.dump(gramGrp_values, outfile, indent=2)

