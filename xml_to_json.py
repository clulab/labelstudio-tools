import json
import anafora
import sys


def parse_element(data):
    data_file = []
    for ann in data.annotations:
        (start, end), = ann.spans
        label_json = {"value": {"start": start, "end": end, "labels": [ann.type]}, "id": ann.id, "from_name": "type",
                      "to_name": "text", "type": "labels"}
        data_file.append(label_json)

        if ann.type == "Between":
            for i in between_type(start, end, ann.properties, ann.id):
                data_file.append(i)
            continue

        for prop_name in ann.properties:
            if ann.properties[prop_name] is not None:

                if prop_name == "Type":
                    data_file.append({"value": {"start": start, "end": end, "choices": [ann.properties["Type"]]},
                                   "id": ann.id, "from_name": ann.type + "-type", "to_name": "text", "type": "choices"})

                elif prop_name == "Value":
                    data_file.append({"value": {"start": start, "end": end, "text": [ann.properties["Value"]]},
                                   "id": ann.id, "from_name": ann.type + "-value", "to_name": "text", "type": "textarea"})

                elif prop_name == "Interval-Type" or prop_name == "Semantics":
                    data_file.append(type_json(start, end, ann.type, ann.properties, prop_name, ann.id))

                elif prop_name == "Periods":
                    periods = ann.properties.xml.findall("./Periods")
                    links = [data.annotations.select_id(period.text) for period in periods]
                    for link in links:
                        prop_periods_json = {"from_id": ann.id, "to_id": link.id, "type": "relation", "labels": ["Period"]}
                        data_file.append(prop_periods_json)

                else:
                    data_file.append(relation_json(ann.properties, ann.id, prop_name))

    return data_file


def relation_json(properties: list, ann_id: str, prop_name: str) -> dict:
    return {"from_id": ann_id, "to_id": properties[prop_name].id, "type": "relation", "labels": [prop_name]}


def type_json(start: int, end: int, ann_type: str, properties: list, tag_type_name: str, ann_id: str) -> dict:
    return {"value": {"start": start, "end": end, "choices": [properties[tag_type_name]]}, "id": ann_id,
                          "from_name": ann_type + "-" + tag_type_name, "to_name": "text", "type": "choices"}


def between_type(start: int, end: int, properties: list, ann_id: str) -> str:
    temp_list = []
    for prop_name in properties:
        if properties[prop_name] is not None:
            if prop_name == "Start-Interval" or prop_name == "End-Interval":
                temp_list.append({"from_id": ann_id, "to_id": properties[prop_name].id, "type": "relation", "labels": ["Interval"]})
            else:
                temp_list.append(between_type_json(start, end, properties, prop_name, ann_id))
    return temp_list


def between_type_json(start: int, end: int, properties: list, prop_name: str, ann_id: str) -> dict:
    return {"value": {"start": start, "end": end, "choices": [properties[prop_name]]}, "id": ann_id,
                        "from_name": prop_name, "to_name": "text", "type": "choices"}


if __name__ == "__main__":
    with open("data.json", "w") as json_file:
        data = anafora.AnaforaData.from_file(sys.argv[1])
        json.dump(parse_element(data), json_file, indent=4)
        json_file.close()


