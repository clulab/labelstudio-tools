import argparse
import ast
import json
import os
from typing import Text, Mapping
import xml.etree.cElementTree as ET


def anafora_to_labelstudio(
        anafora_schema_path: Text,
        anafora_annotations_path: Text,
        labelstudio_path: Text):
    property_types = anafora_schema_to_labelstudio_schema(
        anafora_path=anafora_schema_path,
        labelstudio_path=f"{labelstudio_path}.schema.xml",
    )
    anafora_annotations_to_labelstudio_annotations(
        anafora_path=anafora_annotations_path,
        labelstudio_path=f"{labelstudio_path}.data.json",
        labelstudio_property_types=property_types,
    )


def anafora_schema_to_labelstudio_schema(
        anafora_path: Text,
        labelstudio_path: Text) -> Mapping[Text, Text]:
    # the overall view
    ls_view_elem = ET.Element('View', dict(style="display: flex;"))

    # the view of the label choices
    ls_labels_view_elem = ET.SubElement(ls_view_elem, 'View', dict(
        style="flex: 20%"))
    ls_labels_elem = ET.SubElement(ls_labels_view_elem, 'Labels', dict(
        name="type", toName="text", showInline="false"))
    ls_relations_elem = ET.SubElement(ls_labels_view_elem, 'Relations')
    relation_types = set()

    # the view of the text
    ls_text_view_elem = ET.SubElement(ls_view_elem, 'View', dict(
        style="flex: 60%"))
    ET.SubElement(ls_text_view_elem, 'Text', dict(name="text", value="$text"))

    # the view of the attribute choices
    ls_attrib_view_elem = ET.SubElement(ls_view_elem, 'View', dict(
        style="flex: 20%"))

    an_tree = ET.parse(anafora_path)
    an_root = an_tree.getroot()
    default_attributes = dict(required=False)
    for an_defaults_elem in an_root.iter("defaultattribute"):
        for elem in an_defaults_elem:
            default_attributes[elem.tag] = ast.literal_eval(elem.text)

    def get(attrib, name):
        return attrib.get(name, default_attributes[name])

    ls_property_types = {}
    for an_entities_elem in an_root.iter('entities'):
        entities_type = an_entities_elem.attrib["type"]
        ET.SubElement(ls_labels_elem, 'Header', dict(value=f"{entities_type}:"))
        for an_entity_elem in an_entities_elem.iter('entity'):
            entity_type = an_entity_elem.attrib["type"]
            ls_label_attrib = dict(value=entity_type)
            hotkey = an_entity_elem.attrib.get("hotkey")
            if hotkey is not None:
                ls_label_attrib["hotkey"] = hotkey
            color = an_entity_elem.attrib.get("color")
            if color is not None:
                ls_label_attrib["background"] = f"#{color}"
            ET.SubElement(ls_labels_elem, 'Label', ls_label_attrib)
            for an_property_elem in an_entity_elem.iter('property'):
                property_type = an_property_elem.attrib["type"]
                property_input = an_property_elem.attrib["input"]
                property_required = get(an_property_elem.attrib, "required")
                ls_property_name = f"{entity_type}-{property_type}"
                ls_prop_attrib = dict(
                    visibleWhen="region-selected",
                    whenTagName="type",
                    whenLabelValue=entity_type)

                if property_input == "text":
                    ls_property_types[ls_property_name] = "textarea"
                    ls_prop_elem = ET.SubElement(
                        ls_attrib_view_elem, 'View', ls_prop_attrib)
                    ET.SubElement(ls_prop_elem, 'Header', dict(
                        value=f"{property_type}:"))
                    ls_text_area_attrib = dict(
                        name=ls_property_name,
                        toName="text",
                        perRegion="true")
                    if property_required:
                        ls_text_area_attrib["required"] = "true"
                    ET.SubElement(ls_prop_elem, 'TextArea', ls_text_area_attrib)

                elif property_input == "choice":
                    ls_property_types[ls_property_name] = "choices"
                    ls_prop_elem = ET.SubElement(
                        ls_attrib_view_elem, 'View', ls_prop_attrib)
                    ls_choices_attrib = dict(
                        name=ls_property_name,
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
                    ls_property_types[ls_property_name] = 'relation'
                    if property_type not in relation_types:
                        ET.SubElement(ls_relations_elem, 'Relation', dict(
                            value=property_type))
                        relation_types.add(property_type)

                else:
                    raise ValueError(f'unexpected input_type: {property_input}')

    ls_tree = ET.ElementTree(ls_view_elem)
    ET.indent(ls_tree, space="  ", level=0)
    ls_tree.write(labelstudio_path)
    return ls_property_types


def anafora_annotations_to_labelstudio_annotations(
        anafora_path: Text,
        labelstudio_path: Text,
        labelstudio_property_types: Mapping[Text, Text]):
    text_path, schema, annotator, status, xml = anafora_path.rsplit('.', 4)
    with open(text_path) as text_file:
        text = text_file.read()
    ls_types = labelstudio_property_types
    ls_type_to_value = {"textarea": "text", "choices": "choices"}
    ls_results = []
    ls_meta_info = {"source": os.path.basename(text_path)}

    an_tree = ET.parse(anafora_path)
    an_root = an_tree.getroot()
    an_info_elem = an_root.find('info')
    for an_elem in an_info_elem:
        ls_meta_info[an_elem.tag] = an_elem.text

    an_annotations_elem = an_root.find("annotations")
    for an_elem in an_annotations_elem:
        an_id = an_elem.find("id").text
        an_type = an_elem.find("type").text
        an_parents_type = an_elem.find("parentsType").text

        if an_elem.tag == "entity":
            an_spans = [
                tuple(int(offset) for offset in tuple(span_text.split(",")))
                for span_text in an_elem.find("span").text.split(";")
            ]
            # TODO: handle multiple spans
            [(start, end)] = an_spans
            ls_results.append({
                "value": {
                    "start": start,
                    "end": end,
                    "labels": [an_type],
                },
                "id": an_id,
                "from_name": "type",
                "to_name": "text",
                "type": "labels"
            })
            for an_prop_elem in an_elem.find('properties'):
                an_prop_name = an_prop_elem.tag
                an_prop_value = an_prop_elem.text
                if an_prop_value:
                    ls_property_name = f"{an_type}-{an_prop_name}"
                    ls_property_type = ls_types[ls_property_name]
                    if ls_property_type == 'relation':
                        ls_results.append({
                            "from_id": an_id,
                            "to_id": an_prop_value,
                            "type": "relation",
                            "labels": [an_prop_name],
                        })
                    else:
                        ls_results.append({
                            "value": {
                                "start": start,
                                "end": end,
                                ls_type_to_value[ls_property_type]: [
                                    an_prop_value
                                ],
                            },
                            "id": an_id,
                            "from_name": ls_property_name,
                            "to_name": "text",
                            "type": ls_property_type
                        })

        elif an_elem.tag == "relation":
            # TODO: handle Anafora relations
            raise NotImplementedError
        else:
            raise ValueError(f'unexpected element type: {an_elem.tag}')

    ls_data = [{
        "data": {
            "text": text,
            "meta_info": ls_meta_info
        },
        "annotations": [{"result": ls_results}]
    }]
    with open(labelstudio_path, 'w') as labelstudio_file:
        json.dump(ls_data, labelstudio_file, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("anafora_schema_path")
    parser.add_argument("anafora_annotations_path")
    parser.add_argument("labelstudio_path")
    anafora_to_labelstudio(**vars(parser.parse_args()))
