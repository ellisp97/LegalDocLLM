import unittest
from unittest.mock import patch, mock_open
from lease_entry import LeaseEntry
from parse_data import process_page, PAGE_SIZE, paginate_json_file
from utils import LeaseEntryError


class BaseTestData(unittest.TestCase):
    """
    Base test class to be inherited by all test classes, sets up the test data
    """
    def setUp(self):
        self.invalid_file = ""

        self.invalid_data = [
                    [1, 4, 5],
                    False,
                    123
                ]
        self.invalid_data_entry = {
                "entryNumber": "2",
                "entryDate": "",
                "entryType": "Schedule of Notices of Leases",
                "entryText": self.invalid_data
            }
        self.invalid_json_data = {None}

        self.multiple_space_entry = [
            '26.03.2010      Parking space 10 Landmark     04.03.2010      EGL569610  ',
            'Edged and       West  Tower (basement         999 years from             ',
            'numbered 29 in  level)                        1.1.2009                   ',
            'blue on                                                                  ',
            'supplementary                                                            ',
            'plan 1'
        ]

        self.multiple_note_entry = [
                    "10.09.1987      89H Denmark Hill (Second      03.08.1987      SGL493290  ",
                    "Edged and       Floor Flat)                   125 years from             ",
                    "numbered 30                                   3.8.1987                   ",
                    "(Part of) in                                                             ",
                    "brown                                                                    ",
                    "NOTE 1: A Deed dated 21 May 1992 made between (1) Orbit Housing Association and (2) Carol Jean Pryce is supplemental to the Lease dated 3 August 1987 of 89H Denmark Hill referred to above. It rectifies the lease plan.",
                    "NOTE 2: Copy Deed filed under SGL493290"
                ]

        self.missing_registration_date_and_plan_ref = [
                    "Low Voltage Electricity       25.03.1993                 ",
                    "Distribution System           140 years from             ",
                    "25.3.1993                  ",
                    "NOTE 1: The Lease comprises also other land.",
                    "NOTE 2: Copy Lease filed under SY76788."
                ]

        self.partial_registration_date_and_plan_ref = [
            "land on the south west side   12.10.1915      SYK572479  ",
            "tinted blue     of Grange Mill Lane           999 years from             ",
            "29.09.1915                 ",
            "NOTE: The lease also comprises other land"
        ]

        self.padded_strings_with_dates = [
            "31.08.2016      21 Sheen Road (first and      31.08.2016      TGL461305  ",
            "second floors)                beginning on               ",
            "and including              ",
            "31.8.2016 and              ",
            "ending on and              ",
            "including                  ",
            "30.8.2026"
        ]

        self.no_padding = ['08.02.2011      Parking space 42 (basement    28.01.2011      AGL228935  ',
                           '106 in blue on  level)                        999 years from             ',
                           'the                                           and including              ',
                           'supplementary                                 1.1.2009 until             ',
                           'plan                                          and including              ',
                           '31.12.3007']

        self.schedule_entries_1 = [
            {
                "entryNumber": "1",
                "entryDate": "",
                "entryType": "Schedule of Notices of Leases",
                "entryText": [
                    "24.06.2008      Second Floor Flat, 34         13.06.2008      K941967    ",
                    "edged and       Bluebell Road                 125 years from             ",
                    "numbered 5 in                                 1/1/2007                   ",
                    "blue (part of)"
                ]
            },
            {
                "entryNumber": "2",
                "entryDate": "",
                "entryType": "Schedule of Notices of Leases",
                "entryText": [
                    "09.07.2008      Ground Floor Flat 26          06.06.2008      K942680    ",
                    "edged and       Bluebell Road and garage      125 years from             ",
                    "numbered 5 in                                 1.1.2007                   ",
                    "blue (part of)"
                ]
            },
            {
                "entryNumber": "3",
                "entryDate": "",
                "entryType": "Schedule of Notices of Leases",
                "entryText": [
                    "17.07.2008      36 Bluebell Road              27.06.2008      K943043    ",
                    "Edged and                                     125 years from             ",
                    "numbered 5 in                                 1.1.2007                   ",
                    "blue (part of)"
                ]
            },
            {
                "entryNumber": "4",
                "entryDate": "",
                "entryType": "Cancelled Item - Schedule of Notices of Leases",
                "entryText": [
                    "ITEM CANCELLED on 11 October 2016."
                ]
            },
        ]


class TestParseData(BaseTestData):
    """
    Test the parse_data.py file
    """

    def test_process_page(self):
        processed_page = process_page(self.schedule_entries_1, -1)
        # Note it should only return the first 3 entries as the 4th entry is cancelled
        self.assertEquals(len(processed_page.keys()), len(self.schedule_entries_1[0:3]))

    def test_process_page_with_invalid_data(self):
        processed_page = process_page([self.invalid_data_entry], -1)
        self.assertEquals(len(processed_page.keys()), 0)

    def test_paginate_invalid_file(self):
        with self.assertRaises(FileNotFoundError):
            paginate_json_file(self.invalid_file, PAGE_SIZE)

    @patch("builtins.open", new_callable=mock_open)
    def test_invalid_json(self, mock_file_open):
        file = "invalid_json.json"
        mock_file_open.return_value.read_data = self.invalid_json_data

        result = paginate_json_file(file, PAGE_SIZE)
        mock_file_open.assert_called_once_with(file, 'r')
        self.assertEquals({}, result)



class TestLeaseEntry(BaseTestData):
    """
    Test the LeaseEntry class
    """

    def test_invalid_data(self):
        with self.assertRaises(LeaseEntryError):
            LeaseEntry(self.invalid_data, "", -1)

    def test_parse_data_with_many_spaces(self):
        lease_entry = LeaseEntry(self.multiple_space_entry, "", -1)
        self.assertEqual(lease_entry.registration_date_and_plan_ref, '26.03.2010 Edged and numbered 29 in blue on supplementary plan 1')
        self.assertEqual(lease_entry.property_description, 'Parking space 10 Landmark West Tower (basement level)')
        self.assertEqual(lease_entry.date_of_lease_and_term, "04.03.2010 999 years from 1.1.2009")
        self.assertEqual(lease_entry.lessees_title, 'EGL569610')
        self.assertEqual(lease_entry.notes, None)

    def test_parse_data_with_multiple_notes(self):
        lease_entry = LeaseEntry(self.multiple_note_entry, "", -1)
        self.assertEqual(lease_entry.registration_date_and_plan_ref, '10.09.1987 Edged and numbered 30 (Part of) in brown')
        self.assertEqual(lease_entry.property_description, '89H Denmark Hill (Second Floor Flat)')
        self.assertEqual(lease_entry.date_of_lease_and_term, "03.08.1987 125 years from 3.8.1987")
        self.assertEqual(lease_entry.lessees_title, 'SGL493290')
        self.assertEqual(lease_entry.notes, ['NOTE 1: A Deed dated 21 May 1992 made between (1) Orbit Housing Association and (2) Carol Jean Pryce is supplemental to the Lease dated 3 August 1987 of 89H Denmark Hill referred to above. It rectifies the lease plan.', 'NOTE 2: Copy Deed filed under SGL493290'])

    def test_str_representation(self):
        lease_entry = LeaseEntry(self.multiple_space_entry, "", -1)
        self.assertEqual(lease_entry.__str__(), "Registration date and plan ref: 26.03.2010 Edged and numbered 29 in blue on supplementary plan 1\nProperty description: Parking space 10 Landmark West Tower (basement level)\nDate of lease and term: 04.03.2010 999 years from 1.1.2009\nLessee’s title: EGL569610\n")

    def test_str_representation_with_multiple_notes(self):
        lease_entry = LeaseEntry(self.multiple_note_entry, "", -1)
        self.assertEqual(lease_entry.__str__(), "Registration date and plan ref: 10.09.1987 Edged and numbered 30 (Part of) in brown\nProperty description: 89H Denmark Hill (Second Floor Flat)\nDate of lease and term: 03.08.1987 125 years from 3.8.1987\nLessee’s title: SGL493290\nNote 1: NOTE 1: A Deed dated 21 May 1992 made between (1) Orbit Housing Association and (2) Carol Jean Pryce is supplemental to the Lease dated 3 August 1987 of 89H Denmark Hill referred to above. It rectifies the lease plan.\nNote 2: NOTE 2: Copy Deed filed under SGL493290\n")

    def test_parse_data_with_missing_registration_date_and_plan_ref(self):
        lease_entry = LeaseEntry(self.missing_registration_date_and_plan_ref, "", -1)
        self.assertEqual(lease_entry.registration_date_and_plan_ref, "")
        self.assertEqual(lease_entry.property_description, 'Low Voltage Electricity Distribution System')
        self.assertEqual(lease_entry.date_of_lease_and_term, "25.03.1993 140 years from 25.3.1993")
        self.assertEqual(lease_entry.lessees_title, "")
        self.assertEqual(lease_entry.notes, ['NOTE 1: The Lease comprises also other land.','NOTE 2: Copy Lease filed under SY76788.'])

    def test_parse_data_with_partial_registration_date_and_plan_ref(self):
        lease_entry = LeaseEntry(self.partial_registration_date_and_plan_ref, "", -1)
        self.assertEqual(lease_entry.registration_date_and_plan_ref, "tinted blue")
        self.assertEqual(lease_entry.property_description, "land on the south west side of Grange Mill Lane")
        self.assertEqual(lease_entry.date_of_lease_and_term, "12.10.1915 999 years from 29.09.1915")
        self.assertEqual(lease_entry.lessees_title, "SYK572479")

    def test_padded_strings_with_dates(self):
        lease_entry = LeaseEntry(self.padded_strings_with_dates, "", -1)
        self.assertEqual(lease_entry.registration_date_and_plan_ref, "31.08.2016")
        self.assertEqual(lease_entry.property_description, "21 Sheen Road (first and second floors)")
        self.assertEqual(lease_entry.date_of_lease_and_term, "31.08.2016 beginning on and including 31.8.2016 and ending on and including 30.8.2026")
        self.assertEqual(lease_entry.lessees_title, "TGL461305")




