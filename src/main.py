from concurrency_test import compare_time_difference
from model import get_ai_model
from parse_data import paginate_json_file, PAGE_SIZE
from itertools import chain
import pandas as pd

def save_leases_to_csv(leases: dict):
    """
    Save the leases to a CSV file with the following columns:
    [page_num, entry_id, registration_date_and_plan_ref, property_description, date_of_lease_and_term, lessees_title, notes]
    :param leases:
    :return:
    """
    leases_flattened = list(chain(*[lease for lease_schedule in full_lease_dictionary.values() for lease in lease_schedule.values()]))
    lease_entries_dict_list = [entry.__dict__ for entry in leases_flattened]
    df = pd.DataFrame(lease_entries_dict_list)
    df.to_csv('lease_entries.csv', index=False)


if __name__ == '__main__':
    full_lease_dictionary = paginate_json_file('src/schedule_of_notices_of_lease_examples.json', PAGE_SIZE)
    save_leases_to_csv(full_lease_dictionary)