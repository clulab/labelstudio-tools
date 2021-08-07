import json
import anafora
import sys


def parse_element(data: anafora.AnaforaData, set_to_super_interval=False):
    clean_bad_links(data)

    if set_to_super_interval:
        data = check_year_of_sub_interval(data)
        
    data_file = []
    for ann in data.annotations:

        first_spans = True
        for (start, end) in ann.spans:
            if first_spans:
                label_json = {"value": {"start": start, "end": end, "labels": [ann.type]}, "id": ann.id,
                              "from_name": "type", "to_name": "text", "type": "labels"}
                first_spans = False
            else:
                label_json = {"value": {"start": start, "end": end, "labels": [ann.type]},
                              "id": ann.id.split("@")[0] + "_continued" + ann.id.replace(ann.id.split("@")[0], ""),
                              "from_name": "type", "to_name": "text", "type": "labels"}
            data_file.append(label_json)

        for prop_name in ann.properties:
            if ann.properties[prop_name] is not None:
                if prop_name == "Type":
                    data_file.append({"value": {"start": start, "end": end, "choices": [ann.properties["Type"]]},
                            "id": ann.id, "from_name": ann.type + "-type", "to_name": "text", "type": "choices"})
                elif prop_name == "Value":
                    data_file.append({"value": {"start": start, "end": end, "text": [ann.properties["Value"]]},
                            "id": ann.id, "from_name": ann.type + "-value", "to_name": "text", "type": "textarea"})
                elif prop_name == "Periods" or prop_name == "Repeating-Intervals" \
                        or prop_name == "Intervals" or prop_name == "Sub-Interval":
                    duplicate_relations = ann.properties.xml.findall("./" + prop_name)
                    #links = [data.annotations.select_id(relation.text) for relation in duplicate_relations]
                    links = []
                    for relation in duplicate_relations:
                        links.append(data.annotations.select_id(relation.text))

                    for link in links:
                        data_file.append({"from_id": ann.id, "to_id": link.id, "type": "relation", "labels": [prop_name]})

                elif prop_name.endswith("Interval-Type") or prop_name == "Semantics" or prop_name.endswith("Included"):
                    data_file.append({"value": {"start": start, "end": end, "choices": [ann.properties[prop_name]]},
                            "id": ann.id, "from_name": ann.type + "-" + prop_name, "to_name": "text", "type": "choices"})

                else:
                    data_file.append({"from_id": ann.id, "to_id": ann.properties[prop_name].id, "type": "relation", "labels": [prop_name]})

    if set_to_super_interval:
        data_file = sub_to_super(data_file)

    return data_file


def sub_to_super(json_list: list):
    for sub_elem in json_list:
        if sub_elem["type"] == "relation":
            if sub_elem["labels"][0] == "Sub-Interval":
                temp = sub_elem["from_id"]
                sub_elem["from_id"] = sub_elem["to_id"]
                sub_elem["to_id"] = temp
                sub_elem["labels"][0] = "Super-Interval"
    json_list.sort(key=comp_id)
    return json_list


def comp_id(sub_elem):
    if sub_elem["type"] != "relation":
        if sub_elem["id"].split("@")[0].endswith("_continued"):
            return int(sub_elem["id"].split("@")[0].rstrip("_continued"))
        else:
            return int(sub_elem["id"].split("@")[0])
    elif sub_elem["labels"][0] == "Super-Interval":
        return int(sub_elem["from_id"].split("@")[0])+0.5
    else:
        return int(sub_elem["from_id"].split("@")[0])


def check_year_of_sub_interval(data):
    for ann in data.annotations:
        for prop_name in ann.properties:
            if ann.properties[prop_name] is not None:
                if prop_name == "Type" or prop_name == "Value" or prop_name == "Sub-Interval" \
                        or prop_name.endswith("Interval-Type") or prop_name == "Semantics" or prop_name.endswith("Included"):
                    continue
                elif prop_name == "Periods" or prop_name == "Repeating-Intervals" or prop_name == "Intervals":
                    duplicate_relations = ann.properties.xml.findall("./" + prop_name)
                    for relation in duplicate_relations:
                        link = data.annotations.select_id(relation.text)
                        if link.id != find_sub_root_entity(link).id:
                            smallest_unit = find_sub_root_entity(link)
                            relation.text = smallest_unit.id
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


def clean_bad_links(data: anafora.AnaforaData):
    for annotation in data.annotations:
        invalid = []
        for key, value in annotation.properties.items():
            if isinstance(value, str) and '@' in value:
                invalid.append((key, value))
        for key, value in invalid:
            print(f'Removing invalid link: {annotation.id}/{key}={value}')
            del annotation.properties[key]


if __name__ == "__main__":
    with open("data.json", "w") as json_file:
        data = anafora.AnaforaData.from_file(sys.argv[1])
        json.dump(list(parse_element(data)), json_file, indent=4)
        json_file.close()
        
