from xml.etree import cElementTree as ET
import re, json

source_file = "source/dic.xml"
usg_values = {}

# load dictionary
tree = ET.ElementTree(file=source_file)
dictionary = tree.getroot()
print(f"\nSuccessfully loaded XML source: {source_file}")
for elem in dictionary.findall('.//{http://www.tei-c.org/ns/1.0}usg'):
    if elem.attrib['type'] not in usg_values:
        usg_values[elem.attrib['type']] = {}
    if elem.text not in usg_values[elem.attrib['type']]:
        usg_values[elem.attrib['type']][elem.text] = 1
    else:
        usg_values[elem.attrib['type']][elem.text] += 1

with open("usg_values.json", "w") as outfile:
    json.dump(usg_values, outfile, indent=2)

csv_text = "usg_type\tvalue\n"
for dom in usg_values['domain']:
    csv_text += f"domain\t{dom}\n"
for reg in usg_values['socioCultural']:
    csv_text += f"register\t{reg}\n"
for region in usg_values['geographic']:
    csv_text += f"region\t{region}\n"

with open("usg_values.csv", "w") as outfile:
    outfile.write(csv_text)

