
import argparse
from xml.etree import ElementTree


def remove_some_elements(input_path, output_path):
    file = open(input_path, "r")
    elem = ElementTree.parse(file)
    root = elem.getroot()
    for ele in list(root):
        if ele.tag != "annotations":
            root.remove(ele)

    entities = root.findall(".//entity")
    for entity in entities:
        if entity[2].text == "Event" or entity[2].text == "Time-Zone" \
                or entity[2].text == "PreAnnotation" or entity[2].text == "NotNormalizable":
            entity.remove(entity.find(".//properties"))
        for att in entity:
            if att.tag != "id" and att.tag != "span" and att.tag != "type" and att.tag != "properties":
                entity.remove(att)

    properties = root.findall(".//properties")
    for prop in list(properties):
        for pp in list(prop):
            if not pp.text:
                prop.remove(pp)

    elem.write(output_path, encoding="UTF-8", xml_declaration=True)
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path")
    parser.add_argument("output_path")
    args = parser.parse_args()

    remove_some_elements(**vars(args))


