import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from parse_data import process_page, paginate_json_file, PAGE_SIZE, DEFAULT_SCHEDULE


def process_page_wrapper(page_data):
    return process_page(page_data)


def threaded_paginate_json_file(file_path: str, page_size: int):
    """
    Paginate a json file
    :param file_path: path to the json file
    :param page_size: number of items per page
    """
    full_lease_schedules = {}

    with open(file_path, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            logging.error(f"Error: Unable to decode JSON from {file_path}")
            return {}

        for i, lease_dict in enumerate(data):
            items_processed = 0
            merged_lease_schedule = {}
            lease_schedule = lease_dict["leaseschedule"]

            # if mistaken schedule type, skip
            if lease_schedule["scheduleType"] != DEFAULT_SCHEDULE:
                continue

            with ThreadPoolExecutor(max_workers=10) as executor:
                tasks = []
                while items_processed < len(lease_schedule["scheduleEntry"]):
                    page_data = lease_schedule["scheduleEntry"][items_processed:items_processed + page_size]
                    tasks.append(executor.submit(process_page_wrapper, page_data))
                    items_processed += page_size

                for task in as_completed(tasks):
                    current_lease_dict = task.result()
                    merged_lease_schedule = {**merged_lease_schedule, **current_lease_dict}

            full_lease_schedules[i] = merged_lease_schedule
    return full_lease_schedules


def compare_time_difference():
    start_time = time.time()
    result_non_concurrent = paginate_json_file('schedule_of_notices_of_lease_examples.json', PAGE_SIZE)
    end_time = time.time()
    print("Non-concurrent execution time: {:.2f} seconds".format(end_time - start_time))

    # Concurrent version
    start_time = time.time()
    result_concurrent = threaded_paginate_json_file('schedule_of_notices_of_lease_examples.json', PAGE_SIZE)
    end_time = time.time()
    print("Concurrent execution time: {:.2f} seconds".format(end_time - start_time))
