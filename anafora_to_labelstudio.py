import argparse
import ast
import xml.etree.cElementTree as ET


def anafora_schema_to_labelstudio_schema(anafora_path, labelstudio_path):
    ls_view_elem = ET.Element('View')
    ls_tree = ET.ElementTree(ls_view_elem)
    ls_labels_elem = ET.SubElement(
        ls_view_elem, 'Labels', dict(name="type", toName="text"))
    ls_relations_elem = ET.SubElement(ls_view_elem, 'Relations')
    relation_types = set()

    an_tree = ET.parse(anafora_path)
    an_root = an_tree.getroot()
    default_attributes = dict(required=False)
    for an_defaults_elem in an_root.iter("defaultattribute"):
        for elem in an_defaults_elem:
            default_attributes[elem.tag] = ast.literal_eval(elem.text)

    def get(attrib, name):
        return attrib.get(name, default_attributes[name])

    for an_entity_elem in an_root.iter('entity'):
        entity_type = an_entity_elem.attrib["type"]
        ET.SubElement(ls_labels_elem, 'Label', dict(value=entity_type))
        for an_property_elem in an_entity_elem.iter('property'):
            property_type = an_property_elem.attrib["type"]
            property_input = an_property_elem.attrib["input"]
            property_required = get(an_property_elem.attrib, "required")
            ls_prop_attrib = dict(
                visibleWhen="region-selected",
                whenTagName="type",
                whenLabelValue=entity_type)

            if property_input == "text":
                ls_prop_elem = ET.SubElement(
                    ls_view_elem, 'View', ls_prop_attrib)
                ls_text_area_attrib = dict(
                    name=f"{entity_type}-{property_type}",
                    perRegion="true")
                if property_required:
                    ls_text_area_attrib["required"] = "true"
                ET.SubElement(ls_prop_elem, 'TextArea', ls_text_area_attrib)

            elif property_input == "choice":
                ls_prop_elem = ET.SubElement(
                    ls_view_elem, 'View', ls_prop_attrib)
                ls_choices_attrib = dict(
                    name=f"{entity_type}-{property_type}",
                    toName="text",
                    perRegion="true")
                if property_required:
                    ls_choices_attrib["required"] = "true"
                ls_choices_elem = ET.SubElement(
                    ls_prop_elem, 'Choices', ls_choices_attrib)
                ET.SubElement(ls_choices_elem, 'Header', dict(
                    value=f"{property_type}:"))
                for choice in an_property_elem.text.split(','):
                    if choice:
                        ET.SubElement(ls_choices_elem, 'Choice', dict(
                            value=choice))

            elif property_input == "list":
                if property_type not in relation_types:
                    ET.SubElement(ls_relations_elem, 'Relation', dict(
                        value=property_type))
                    relation_types.add(property_type)

            else:
                raise ValueError(f'unexpected input_type: {property_input}')

    ET.indent(ls_tree, space="  ", level=0)
    ls_tree.write(labelstudio_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    schema_parser = subparsers.add_parser("schema")
    schema_parser.set_defaults(func=anafora_schema_to_labelstudio_schema)
    schema_parser.add_argument("anafora_path", metavar="anafora_xml")
    schema_parser.add_argument("labelstudio_path", metavar="labelstudio_xml")
    kwargs = vars(parser.parse_args())
    kwargs.pop("func")(**kwargs)
