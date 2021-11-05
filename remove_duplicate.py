import anafora
import argparse
import os
from collections import Counter


def main(input_dir, output_dir):

    paths = anafora.walk(input_dir, xml_name_regex=r'TimeNorm\.gold\.completed')
    for sub_dir, text_file_name, xml_file_names in paths:
        for xml_file_name in xml_file_names:
            input_path = os.path.join(input_dir, sub_dir, xml_file_name)
            data = anafora.AnaforaData.from_file(input_path)

            # find entities that share the same type and span
            counts = Counter()
            for entity in data.annotations:
                counts[entity] += 1

            duplicates = {key for key, count in counts.items() if count > 1}

            identical_span_to_parent_entity = {}  # same spans with different id
            remove_id = []
            # which types most often have duplicated entities as arguments
            for entity in data.annotations:
                for _, value in entity.properties.items():
                    if isinstance(value, anafora.AnaforaAnnotation) and value in duplicates:
                        if value.spans not in identical_span_to_parent_entity:
                            identical_span_to_parent_entity[value.spans] = value.id
                        else:
                            remove_id.append(value.id)
                            entity.properties['Super-Interval'] = identical_span_to_parent_entity[value.spans]
                        break

            for entity in list(data.annotations):
                if entity.id in remove_id:
                    data.annotations.remove(entity)

            output_parent = os.path.join(output_dir, sub_dir)
            if not os.path.exists(output_parent):
                os.makedirs(output_parent)
            data.to_file(os.path.join(output_parent, xml_file_name))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    parser.add_argument("output_dir")
    args = parser.parse_args()

    main(**vars(args))

