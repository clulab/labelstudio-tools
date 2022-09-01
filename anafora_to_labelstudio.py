import argparse
import ast
import json
import os
import re
from typing import Any, Text, Mapping
import xml.etree.cElementTree as ET


def anafora_to_labelstudio(
        anafora_path: Text,
        labelstudio_path: Text,
        annotator: Text,
        status: Text,
        project: Text):

    an_setting_tree = ET.parse(os.path.join(anafora_path, ".setting.xml"))
    an_setting_root = an_setting_tree.getroot()
    for an_schema_elem in an_setting_root.findall("./schemas/schema"):
        an_schema_name = an_schema_elem.attrib["name"]
        an_schema_named_paths = []
        an_schema_path = an_schema_elem.findtext("file")
        if an_schema_path:
            an_schema_named_paths.append((an_schema_name, an_schema_path))
        for an_mode_elem in an_schema_elem.iter('mode'):
            an_mode_name = an_mode_elem.attrib["name"]
            an_schema_path = an_mode_elem.find("file").text
            an_mode_name = f"{an_schema_name}-{an_mode_name}"
            an_schema_named_paths.append((an_mode_name, an_schema_path))

        for an_name, an_schema_path in an_schema_named_paths:
            an_schema_path = os.path.join(anafora_path, ".schema", an_schema_path)
            if os.path.exists(an_schema_path):
                ls_tree, ls_property_types = anafora_schema_to_labelstudio_schema(
                    anafora_path=an_schema_path,
                )
                ET.indent(ls_tree, space="  ", level=0)
                ls_tree.write(f"{labelstudio_path}.{an_schema_name}.schema.xml")

                ls_data = []
                an_filename_matcher = re.compile(
                    f".*[.]{an_schema_name}[.]{annotator}[.]{status}[.]xml")
                for dirpath, dirnames, filenames in os.walk(anafora_path):
                    if project is None or project in dirpath:
                        for filename in filenames:
                            if an_filename_matcher.match(filename):
                                print(filename)
                                ls_data.append(anafora_annotations_to_labelstudio_annotations(
                                    anafora_path=os.path.join(anafora_path, dirpath, filename),
                                    labelstudio_property_types=ls_property_types,
                                ))

                with open(f"{labelstudio_path}.{an_schema_name}.data.json", 'w') as labelstudio_file:
                    json.dump(ls_data, labelstudio_file, indent=4)


def anafora_schema_to_labelstudio_schema(
        anafora_path: Text) -> tuple[ET.ElementTree, Mapping[Text, Text]]:
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
    return ls_tree, ls_property_types


def anafora_annotations_to_labelstudio_annotations(
        anafora_path: Text,
        labelstudio_property_types: Mapping[Text, Text]) -> Mapping[Text, Any]:
    text_path, schema, annotator, status, xml = anafora_path.rsplit('.', 4)
    try:
        with open(text_path) as text_file:
            text = text_file.read()
    except FileNotFoundError as e:
        text = None
        print(f"WARNING: {e}")
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
            for i, (start, end) in enumerate(an_spans):
                an_revised_id = an_id if i == 0 else f"{an_id}-{i}"
                ls_results.append({
                    "value": {
                        "start": start,
                        "end": end,
                        "labels": [an_type],
                    },
                    "id": an_revised_id,
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
                                "from_id": an_revised_id,
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
                                "id": an_revised_id,
                                "from_name": ls_property_name,
                                "to_name": "text",
                                "type": ls_property_type
                            })

        elif an_elem.tag == "relation":
            # TODO: handle Anafora relations
            raise NotImplementedError
        else:
            raise ValueError(f'unexpected element type: {an_elem.tag}')

    return {
        "data": {
            "text": text,
            "meta_info": ls_meta_info
        },
        "annotations": [{"result": ls_results}]
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("anafora_path")
    parser.add_argument("labelstudio_path")
    parser.add_argument("--annotator", default="gold")
    parser.add_argument("--status", default="completed")
    parser.add_argument("--project")
    anafora_to_labelstudio(**vars(parser.parse_args()))
