import json
import logging
from collections import defaultdict
from typing import List
from lease_entry import LeaseEntry
from utils import EntryTypes, LeaseEntryError

PAGE_SIZE = 100
DEFAULT_SCHEDULE = "SCHEDULE OF NOTICES OF LEASE"

# Add logging to the console if we were to use this in a production environment
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[
        logging.StreamHandler(),  # Log to the console
    ]
)


def process_page(page_data: List[dict], page_num: int) -> dict:
    """
    Process the page_data separated by the page_size
    :param page_data: list of items to process

    :return: dictionary of lease entry objects
    """
    lease_dict = defaultdict(list)
    for entry in page_data:
        if entry["entryType"] == EntryTypes.CANCELLED_ITEM_SCHEDULE_OF_NOTICES_OF_LEASES.value:
            continue
        try:
            lease_entry = LeaseEntry(data=entry["entryText"], entry_id=entry["entryNumber"], page_num=page_num)
        except LeaseEntryError:
            logging.error(
                f"Invalid data received, row is being skipped for the entryText: {entry['entryText']}")
            continue
        lease_dict[entry["entryNumber"]].append(lease_entry)
    return lease_dict


def paginate_json_file(file_path: str, page_size: int) -> dict:
    """
    Parse all the data from the json file, paginating based on the length of the schedule entry
    :param file_path: path to the json file
    :param page_size: number of items per page

    :return: dictionary of dictionaries, where the first key is the index of the leaseschedule how it appears in the json
    """
    full_lease_schedules = {}

    with open(file_path, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            logging.error(f"Error: Unable to decode JSON from {file_path}")
            return {}

        for i, lease_dict in enumerate(data):
            logging.info(f"Processing lease schedule {i}")
            items_processed = 0
            merged_lease_schedule = {}
            lease_schedule = lease_dict["leaseschedule"]

            # if mistaken schedule type, skip
            if lease_schedule["scheduleType"] != DEFAULT_SCHEDULE:
                continue

            # Paginate the data based on the number of entries in the schedule
            while items_processed < len(lease_schedule["scheduleEntry"]):
                logging.info(f"Processing page {items_processed // page_size}")
                page_data = lease_schedule["scheduleEntry"][items_processed:items_processed + page_size]
                current_lease_dict = process_page(page_data, i)
                merged_lease_schedule = {**merged_lease_schedule, **current_lease_dict}
                items_processed += page_size

            full_lease_schedules[i] = merged_lease_schedule
    return full_lease_schedules
