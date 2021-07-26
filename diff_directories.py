
from xml_to_json import parse_element
from json_to_xml import parse_json
from simplify_golden_file import remove_some_elements

import anafora
import argparse
import os


def compare_through_golden_files(input_dir):
    paths = anafora.walk(input_dir, xml_name_regex=r'TimeNorm\.gold\.completed')

    for sub_dir, text_file_name, xml_file_names in paths:
        for xml_file_name in xml_file_names:
            input_path = os.path.join(input_dir, sub_dir, xml_file_name)
            data = anafora.AnaforaData.from_file(input_path)
            data = parse_json(parse_element(data))
            data.to_file("output_from_labelstud.xml")
            remove_some_elements(input_path, "output_from_golden.xml")
            compare_two_files("output_from_labelstud.xml", "output_from_golden.xml", xml_file_name)

    return


def compare_two_files(labelstudio_output_path: str,  golden_file_output_path: str, error_output_xml_file_name: str):
    labelstudio_file_str = open(labelstudio_output_path, "r").read().replace('\n', '').replace('\t', '')
    golden_file_str = open(golden_file_output_path, "r").read().replace('\n', '').replace('\t', '')

    if labelstudio_file_str != golden_file_str:
        print(f"two files are not equal {error_output_xml_file_name} !\n")
        print("******************************************************")

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    args = parser.parse_args()

    compare_through_golden_files(**vars(args))
