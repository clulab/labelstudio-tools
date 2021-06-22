import json
import anafora
import sys


set_to_super_interval = False


def parse_element(data):
    data_file = []
    for ann in data.annotations:
        (start, end), = ann.spans
        label_json = {"value": {"start": start, "end": end, "labels": [ann.type]}, "id": ann.id, "from_name": "type",
                      "to_name": "text", "type": "labels"}
        data_file.append(label_json)

        for prop_name in ann.properties:
            if ann.properties[prop_name] is not None:
                if prop_name == "Type":
                    data_file.append({"value": {"start": start, "end": end, "choices": [ann.properties["Type"]]},
                            "id": ann.id, "from_name": ann.type + "-type", "to_name": "text", "type": "choices"})
                elif prop_name == "Value":
                    data_file.append({"value": {"start": start, "end": end, "text": [ann.properties["Value"]]},
                            "id": ann.id, "from_name": ann.type + "-value", "to_name": "text", "type": "textarea"})

                elif prop_name == "Periods":
                    periods = ann.properties.xml.findall("./Periods")
                    links = [data.annotations.select_id(period.text) for period in periods]
                    for link in links:
                        prop_periods_json = {"from_id": ann.id, "to_id": link.id, "type": "relation", "labels": ["Periods"]}
                        data_file.append(prop_periods_json)

                elif prop_name.endswith("Interval-Type") or prop_name == "Semantics" or prop_name.endswith("Included"):
                    data_file.append({"value": {"start": start, "end": end, "choices": [ann.properties[prop_name]]},
                            "id": ann.id, "from_name": ann.type + "-" + prop_name, "to_name": "text", "type": "choices"})

                else:
                    link_entity = ann.properties[prop_name]
                    if prop_name == "Sub-Interval" and set_to_super_interval:
                        data_file.append({"from_id": link_entity.id, "to_id": ann.id, "type": "relation", "labels": ["Super-Interval"]})
                    else:
                        data_file.append({"from_id": ann.id, "to_id": link_entity.id, "type": "relation", "labels": [prop_name]})

    return data_file


if __name__ == "__main__":
    with open("data.json", "w") as json_file:
        data = anafora.AnaforaData.from_file(sys.argv[1])
        #set_to_super_interval = True
        json.dump(list(parse_element(data)), json_file, indent=4)
        json_file.close()
