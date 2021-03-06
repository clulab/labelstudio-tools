
import json
import anafora
import sys
from xml.etree import ElementTree


def parse_json(input_dict):
    data = anafora.AnaforaData()
    list_of_entity_index = get_entity_index(input_dict)

    for i in range(len(list_of_entity_index)-1):
        entity = build_an_entity(input_dict[list_of_entity_index[i]])
        # when an entity has more than one group of span
        if i < len(list_of_entity_index)-2 \
                and input_dict[list_of_entity_index[i]+1]["type"] == "labels"\
                and input_dict[list_of_entity_index[i]+1]["id"].split("@")[0].endswith("_continued"):
            multiple_spans(entity, input_dict[list_of_entity_index[i] + 1])
            entity.properties = set_up_properties(input_dict, list_of_entity_index[i] + 2, list_of_entity_index[i + 1], entity)

        else:
            entity.properties = set_up_properties(input_dict, list_of_entity_index[i]+1, list_of_entity_index[i+1], entity)

        data.annotations.append(entity)
    data.indent()
    return data


def build_an_entity(current_label: list):
    entity = anafora.AnaforaEntity()
    entity.id = current_label["id"]
    entity.spans = (current_label["value"]["start"], current_label["value"]["end"]),
    entity.type = current_label["value"]["labels"][0]
    return entity


def multiple_spans(entity, another_spans):
    first_span_start = entity.spans[0][0]
    first_span_end = entity.spans[0][1]
    second_span_start = another_spans["value"]["start"]
    second_span_end = another_spans["value"]["end"]
    entity.spans = ((first_span_start, first_span_end), (second_span_start, second_span_end))


def set_up_properties(json_dict_input, start, end, entity):

    for j in range(start, end):

        if json_dict_input[j]["type"] == "choices":
            if json_dict_input[j]["from_name"].endswith("-type"):
                entity.properties["Type"] = json_dict_input[j]["value"]["choices"][0]
            elif json_dict_input[j]["from_name"].endswith("Interval-Type") \
                    or json_dict_input[j]["from_name"].endswith("Semantics") \
                    or json_dict_input[j]["from_name"].endswith("-Included"):
                prop_name = json_dict_input[j]["from_name"].lstrip(entity.type + "-")
                entity.properties[prop_name] = json_dict_input[j]["value"]["choices"][0]

        elif json_dict_input[j]["type"] == "textarea" and json_dict_input[j]["from_name"].endswith("-value"):
            entity.properties["Value"] = json_dict_input[j]["value"]["text"][0]

        elif json_dict_input[j]["labels"][0] == "Periods" \
                or json_dict_input[j]["labels"][0] == "Repeating-Intervals" \
                or json_dict_input[j]["labels"][0] == "Intervals" \
                or json_dict_input[j]["labels"][0] == "Sub-Interval":
            if entity.properties.xml is None:
                entity.properties.xml = ElementTree.SubElement(entity.xml, "properties")
            prop_name = json_dict_input[j]["labels"][0]
            duplicate_relation_elem = ElementTree.SubElement(entity.properties.xml, prop_name)
            duplicate_relation_elem.text = json_dict_input[j]["to_id"]

        elif json_dict_input[j]["type"] == "relation":
            entity.properties[json_dict_input[j]["labels"][0]] = json_dict_input[j]["to_id"]

    return entity.properties


def get_entity_index(list_of_dict):
    list_of_entity_index = []

    for i in range(0, len(list_of_dict)):
        if list_of_dict[i]["type"] == "labels":
            if not list_of_dict[i]["id"].split("@")[0].endswith("_continued"):
                list_of_entity_index.append(i)
    list_of_entity_index.append(len(list_of_dict))

    return list_of_entity_index


if __name__ == "__main__":
    json_input = json.load(open(sys.argv[1]))
    data_object = parse_json(json_input)
    data_object.to_file("data.xml")

