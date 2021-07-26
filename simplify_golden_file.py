
import argparse
import xml.etree.ElementTree as et


def remove_some_elements(input_path, output_path):
    file = open(input_path, "r")
    elem = et.parse(file)
    root = elem.getroot()

    for ele in list(root):
        if ele.tag != "annotations":
            root.remove(ele)

    annotations = root.find(".//annotations")
    if len(annotations) == 0:
        root.remove(annotations)

    entities = root.findall(".//entity")
    for entity in entities:
        for att in entity:
            if att.tag != "id" and att.tag != "span" and att.tag != "type":
                entity.remove(att)
        properties_xml = entity.find(".//properties")
        to_remove = []
        for child in properties_xml:
            if child.text is None or not child.text.strip():
                to_remove.append(child)
        for child in to_remove:
            properties_xml.remove(child)
        if len(properties_xml) == 0:
            entity.remove(properties_xml)

    elem.write(output_path, encoding="UTF-8", xml_declaration=True)
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path")
    parser.add_argument("output_path")
    args = parser.parse_args()

    remove_some_elements(**vars(args))
