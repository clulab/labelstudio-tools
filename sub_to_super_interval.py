
import anafora
import argparse
import os


def sub_to_super(input_dir, output_dir):
    paths = anafora.walk(input_dir, xml_name_regex=r'TimeNorm\.gold\.completed')
    for sub_dir, text_file_name, xml_file_names in paths:
        for xml_file_name in xml_file_names:
            input_path = os.path.join(input_dir, sub_dir, xml_file_name)
            data = anafora.AnaforaData.from_file(input_path)
            data = check_year_of_sub_interval(data)
            for entity in data.annotations:
                if 'Sub-Interval' in entity.properties:
                    sub_entity = entity.properties['Sub-Interval']
                    if sub_entity:
                        sub_entity.properties['Super-Interval'] = entity.id
                    del entity.properties['Sub-Interval']
            output_parent = os.path.join(output_dir, sub_dir)
            if not os.path.exists(output_parent):
                os.makedirs(output_parent)
            data.to_file(os.path.join(output_parent, xml_file_name))


def check_year_of_sub_interval(data):
    for ann in data.annotations:
        for prop_name in ann.properties:
            if ann.properties[prop_name] is not None:
                if prop_name == "Type" or prop_name == "Value" or prop_name == "Sub-Interval":
                    continue
                elif prop_name == "Periods" or prop_name == "Repeating-Intervals" or prop_name == "Intervals":
                    duplicate_relations = ann.properties.xml.findall("./" + prop_name)
                    for relation in duplicate_relations:
                        link = data.annotations.select_id(relation.text)
                        if link.id != find_sub_root_entity(link).id:
                            smallest_unit = find_sub_root_entity(link)
                            relation.text = smallest_unit.id
                elif prop_name.endswith("Interval-Type") or prop_name == "Semantics" or prop_name.endswith("Included"):
                    continue
                else:
                    smallest_unit = find_sub_root_entity(ann.properties[prop_name])
                    ann.properties[prop_name] = smallest_unit

    return data


def find_sub_root_entity(biggest_entity):
    root_entity = biggest_entity
    while root_entity is not None:
        if 'Sub-Interval' not in root_entity.properties or not root_entity.properties["Sub-Interval"]:
            break
        else:
            root_entity = root_entity.properties["Sub-Interval"]
    return root_entity


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    parser.add_argument("output_dir")
    args = parser.parse_args()

    sub_to_super(**vars(args))
