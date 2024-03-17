from dicom_sr_builder.content_sequence_generator import TEXT_generator, NUM_generator, CodeSequence_generator, \
    CODE_generator
from dicom_sr_builder.sr_builder import SRBuilder
import pydicom


class AnalysisSRBuilder:
    def __init__(self, path_analysis_target_file: str, purpose: str):
        self.path_analysis_target_file = path_analysis_target_file
        self.purpose = {"CodeValue": "5000",
                        "CodingSchemeDesignator": "CUSTOM",
                        "CodeMeaning": purpose}
        self.values_list = []
        self.sr = None

    def get_sr(self):
        assert self.sr is not None, "SR not built yet."
        return self.sr.dicom_sr

    def add_values(self, values: list):
        """
        Add values to the list of values
        Each value must be a list of 4 elements (name, list of subtypes, value, unit)
        :param values:
        :return:
        """
        for value in values:
            assert self.check_value_format(value), "Value format is not correct"
        self.values_list.extend(values)

    @staticmethod
    def check_value_format(value):
        assert len(value) == 4, "Value must be a list of 4 elements (name, list of subtypes, value, unit)"
        assert isinstance(value[0], str), "Name must be a string"
        assert isinstance(value[1], list), "Subtypes must be a list"
        assert isinstance(value[2], (int, float)), "Value must be a number"
        assert isinstance(value[3], str), "Unit must be a string"

    def build(self):
        content_sequences = self._generate_sr_content_sequence_for_list_of_values(self.values_list)
        content_sequence_items = []
        for content_sequence in content_sequences:
            content_sequence_items.append(content_sequence.BuildDictionary())
        whole_content_sequence = {"ValueType": "CONTAINER",
                                  "ConceptNameCodeSequence": {"CodeValue": "100",
                                                              "CodingSchemeDesignator": "CUSTOM",
                                                              "CodeMeaning": "Radiobiology Quantities"},
                                  "ContinuityOfContent": "SEPERATE",
                                  "Value": content_sequence_items}
        sr_builder = SRBuilder(self.path_analysis_target_file, self.purpose)
        sr_builder.add_content_sequence(whole_content_sequence)
        sr_builder.build()
        self.sr = sr_builder

    def save_sr_to(self, file_path: str):
        assert self.sr is not None, "SR not built yet."
        self.sr.save_sr_to(file_path)

    def _generate_sr_content_sequence_for_list_of_values(self, list_of_values, it=0):
        """

        :param list_of_values:
        :param it:
        :return:
        """
        all_code_sequence = []
        subtypes_dict = {}
        for value in list_of_values:
            try:
                current_subtype = value[1][it]
                if current_subtype not in subtypes_dict.keys():
                    subtypes_dict[current_subtype] = [value]
                else:
                    subtypes_dict[current_subtype].append(value)

            except IndexError:
                if len(all_code_sequence) == 0:
                    name_squence = TEXT_generator("HAS PROPERTIES", value[0],
                                                  CodeSequence_generator("1", "CUSTOM",
                                                                         "Value Name"))
                    all_code_sequence.append(name_squence)
                value_sequence = NUM_generator("HAS PROPERTIES",
                                               CodeSequence_generator("2", "CUSTOM",
                                                                      "Quantity Value"),
                                               CodeSequence_generator(value[-1], "CUSTOM",
                                                                      "Units"),
                                               value.value[-2])

                all_code_sequence.append(value_sequence)
        for key, sub_list_of_values in subtypes_dict.items():
            if it == 0:
                code_sequence = CODE_generator("HAS PROPERTIES",
                                               CodeSequence_generator("4", "CUSTOM",
                                                                      "Type of Quantity"),
                                               CodeSequence_generator("5", "CUSTOM",
                                                                      key),
                                               self._generate_sr_content_sequence_for_list_of_values(
                                                   sub_list_of_values, it + 1))
            else:
                code_sequence = CODE_generator("HAS PROPERTIES",
                                               CodeSequence_generator("4", "CUSTOM",
                                                                      "Subtype of Quantity"),
                                               CodeSequence_generator("6", "CUSTOM", key),
                                               self._generate_sr_content_sequence_for_list_of_values(
                                                   sub_list_of_values, it + 1))
            all_code_sequence.append(code_sequence)

        return all_code_sequence

    def extract_all_values_from_existing_sr(self, path_to_sr_file):
        """

        :param path_to_sr_file:
        :return:
        """
        open_dicom = pydicom.dcmread(path_to_sr_file)
        instance_meta = open_dicom.to_json_dict()
        content_sequence = instance_meta["0040A730"]["Value"]
        all_values_with_subtypes = self._get_all_values_from_list_of_content_sequence(content_sequence)
        return all_values_with_subtypes

    def get_values_from_value_name_in_existing_sr(self, path_to_sr_file, list_of_value_names, list_of_subtypes=None):
        """
        Get all values from an existing SR file based on the requested value names. If subtypes are provided, only the
        values with the same subtypes will be returned.
        :param path_to_sr_file:
        :param list_of_value_names: list of value names
        :param list_of_subtypes: list of subtypes for each value name
        :return:
        """
        all_values = self.extract_all_values_from_existing_sr(path_to_sr_file)
        found_value_dict = {}
        for values in all_values:
            if values[0] in list_of_value_names:
                if list_of_subtypes is not None:
                    if values[1] == list_of_subtypes[list_of_value_names.index(values[0])]:
                        if values[0] not in found_value_dict.keys():
                            found_value_dict[values[0]] = []
                        found_value_dict[values[0]].append(values)
                else:
                    if values[0] not in found_value_dict.keys():
                        found_value_dict[values[0]] = []
                    found_value_dict[values[0]].append(values)

    def _get_all_values_from_list_of_content_sequence(self, list_of_content_sequence, previous_subtype=[]):
        """
        Get all values from a list of content sequence

        :param list_of_content_sequence:
        :param previous_subtype:
        :return:
        """
        all_values_with_subtypes = []
        name = None
        value = []
        units = []
        for item in list_of_content_sequence:
            if item["0040A040"]["Value"][0] == "CODE":
                all_sub_types = previous_subtype + [item["0040A168"]["Value"][0]["00080104"]["Value"][0]]
                values_with_subtypes = self._get_all_values_from_list_of_content_sequence(item["0040A730"]["Value"],
                                                                                          all_sub_types)
                all_values_with_subtypes += values_with_subtypes
            elif item["0040A040"]["Value"][0] == "TEXT":
                name = item["0040A160"]["Value"][0]
            elif item["0040A040"]["Value"][0] == "NUM":
                value.append(float(item["0040A300"]["Value"][0]["0040A30A"]["Value"][0]))
                units.append(item["0040A300"]["Value"][0]["004008EA"]["Value"][0]["00080100"]["Value"][0])
            else:
                continue
        if name is not None and value != [] and units is not None:
            it = 0
            for each_value in value:
                all_values_with_subtypes.append((name, previous_subtype, each_value, units[it]))
                it += 1

        return all_values_with_subtypes
