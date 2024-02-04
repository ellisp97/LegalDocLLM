from typing import List
import re
from utils import LeaseEntryError

# From browsing the data, I noticed that the maximum length of a line is 73 characters
LINE_LENGTH = 73


class LeaseEntry:
    """
    Class to represent a single lease entry
    """
    page_num = None
    entry_id = None

    registration_date_and_plan_ref = None
    property_description = None
    date_of_lease_and_term = None
    lessees_title = None
    notes = None

    def __init__(self, data: List[str], entry_id: str, page_num: int):
        try:
            self.page_num = page_num
            self.entry_id = entry_id
            parsed_data = self.__parse_input_data(data)
            self.__parse_output_data(parsed_data)
        except (ValueError, AttributeError, TypeError) as e:
            raise LeaseEntryError(e)

    def __str__(self):
        """
        Return a string representation of the lease entry in accordance with the tech task spec
        :return: string representation of the lease entry
        """
        lease_entry = f"Registration date and plan ref: {self.registration_date_and_plan_ref}\n" \
               f"Property description: {self.property_description}\n" \
               f"Date of lease and term: {self.date_of_lease_and_term}\n" \
               f"Lessee’s title: {self.lessees_title}\n"
        if self.notes:
            for i, note in enumerate(self.notes):
                lease_entry += f"Note {i+1}: {note}\n"
        return lease_entry

    def __parse_output_data(self, parsed_data: dict):
        """
        Parse the parsed_data dictionary and assign the values to the class attributes
        :param parsed_data: dictionary of columns and their values
        """
        for key, value in parsed_data.items():
            if value:
                value = value.strip()

            if key == 0:
                self.registration_date_and_plan_ref = value
            elif key == 1:
                self.property_description = value
            elif key == 2:
                self.date_of_lease_and_term = value
            elif key == 3:
                self.lessees_title = value
            elif key.startswith('Note'):
                self.notes = self.notes or []
                self.notes.append(value)

    @staticmethod
    def __find_index_and_words(s: str) -> List[tuple]:
        """
        Separate the string by spaces and return the index of each word
        :param s: string to separate by spaces
        :return: list of tuples containing the index of the word and the word itself
        """
        pattern = r"\S+(?:\s\S+)*"
        matches = [(match.start(), match.group()) for match in re.finditer(pattern, s)]

        # Check if there are matches and the string starts with spaces
        if len(matches) < 4 and s.startswith(' '):
            matches.insert(0, (0, ""))  # Insert (0, "") at the beginning

        return matches

    def __merge_closest_words(self, index_and_words: List[tuple], text: str) -> List[tuple]:
        """
        Merge the closest words together until there are only 4 columns. This is done by finding the 2 entries
        with the smallest distance between them and merging them together.
        :param index_and_words: list of tuples containing the index of the word and the word itself
        :param text: string to merge the words from
        :return: smaller list of tuples containing the index of the word and the word itself
        """
        while len(index_and_words) > 4:
            min_index = self.__find_min_distance(index_and_words)
            merged_word = text[index_and_words[min_index][0]:index_and_words[min_index + 1][0] + len(index_and_words[min_index + 1][1])]
            merged_item = (index_and_words[min_index][0], merged_word)
            index_and_words[min_index] = merged_item
            index_and_words.pop(min_index+1)

        return index_and_words

    @staticmethod
    def __find_min_distance(word_indices):
        """
        Find the 2 words with the smallest distance between them.
        :param word_indices: list of tuples containing the index of the word and the word itself

        :return: index of the word with the smallest distance
        """
        min_distance = float('inf')
        min_index = -1

        for i in range(len(word_indices) - 1):
            distance = word_indices[i + 1][0] - (word_indices[i][0] + len(word_indices[i][1]))
            if distance < min_distance:
                min_distance = distance
                min_index = i

        return min_index

    def __parse_input_data(self, entry_text: List[str]) -> dict:
        """
        Build a dictionary of columns and their values from the entry text
        Utilises the __find_values_and_positions method to find the index of each word in the string`

        :param entry_text: list of strings representing the entry text

        :return: dictionary of columns and their values
        """
        columns = {i: "" for i in range(4)}
        index_to_word = {}
        note_count = 0
        padding_length = 0

        for i, text in enumerate(entry_text):
            # Skip empty lines
            if not text:
                continue

            if text.startswith("NOTE"):
                note_count += 1
                columns[f'Note {note_count}'] = text.strip()
                continue

            # Apply padding to the text if the previous line ended with a space
            # This is to ensure that the columns are aligned correctly
            if text[-1] == " ":
                padding_length = LINE_LENGTH - len(text)

            text = text.rjust(len(text) + padding_length)

            # If there are ever 5 columns at the start of the entry text, we know that a column has been
            # split into multiple columns as there are spaces inbetween
            values_and_positions = self.__find_index_and_words(text)
            if len(values_and_positions) > 4:
                values_and_positions = self.__merge_closest_words(values_and_positions, text)

            # Enumerate over the starting index of the word and the word itself
            # j is the column index
            for j, (pos, value) in enumerate(values_and_positions):
                if i == 0:
                    index_to_word[pos] = j
                    column_index = j
                else:
                    if pos in index_to_word:
                        column_index = index_to_word[pos]
                    else:
                        # If the index is not a key in the index_to_word dictionary, this means the columns
                        # have become misaligned. We need to find the closest index to the current index
                        pos = min(index_to_word, key=lambda k: abs(pos - k))
                        column_index = index_to_word[pos]

                # Avoid adding a second date to the registration_date_and_plan_ref column
                # second date will be added to the date_of_lease_and_term column
                if ((i > 0 and column_index == 0) or (column_index == 1)) and re.match(r"^\d{1,2}[/\.]\d{1,2}[/\.]\d{4}$", value):
                    column_index = 2

                columns[column_index] += " " + value

            # Remove the leases title column after parsing the first line
            # This is because the leases title column is normally a NGL855062 type string
            if i == 0 and len(index_to_word) == 4:
                index_to_word.pop(max(index_to_word, key=index_to_word.get))

        return columns
