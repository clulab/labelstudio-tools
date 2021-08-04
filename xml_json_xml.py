
import anafora
import argparse
import os
from xml_to_json import parse_element
from json_to_xml import parse_json


def xml_json_xml(input_dir, output_dir, set_to_super_interval):
    paths = anafora.walk(input_dir, xml_name_regex=r'TimeNorm\.gold\.completed')
    for sub_dir, text_file_name, xml_file_names in paths:
        for xml_file_name in xml_file_names:
            input_path = os.path.join(input_dir, sub_dir, xml_file_name)
            data = anafora.AnaforaData.from_file(input_path)
            data = parse_json(parse_element(data, set_to_super_interval))
            output_parent = os.path.join(output_dir, sub_dir)
            if not os.path.exists(output_parent):
                os.makedirs(output_parent)
            data.to_file(os.path.join(output_parent, xml_file_name))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    parser.add_argument("output_dir")
    parser.add_argument('--set_to_super_interval', default=False, action='store_true')
    args = parser.parse_args()

    xml_json_xml(**vars(args))
