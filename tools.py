from collections import defaultdict
import urllib.request
import json
import time
import sys
import os
import io
import gc


def default_filter(entry): return entry['main']['document_type']['id'] == 1


def filter_data(data, some_filter=default_filter):
    return filter(some_filter, data)


def progress_hook(count, block_size, total_size):
    global start_time
    if count == 0:
        start_time = time.time()
        return
    duration = time.time() - start_time
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * duration))
    percent = int(count * block_size * 100 / total_size)
    sys.stdout.write('\r %d%%, %d MB, %d KB/s, %d seconds passed' %
                     (percent, progress_size / (1024 * 1024), speed, duration))
    sys.stdout.flush()


def get_json(filename='declarations.json', update=False):
    if update == True:
        os.remove(filename)

    data = None
    try:
        with open(filename, 'rt') as file:
            data = json.loads(file.read())
    except FileNotFoundError:
        print('Downloading data...')
        url = 'https://declarator.org/media/dumps/declarations.json'
        urllib.request.urlretrieve(url, filename, progress_hook)
        print('\nDone.')
        data = get_json(filename)

    data = filter_data(data)
    # data = filter_data(data, lambda e: e['main']['year'] == 2018)
    gc.collect()

    return data


def get_cars(filename='carbrand.json', update=False):
    if update == True:
        os.remove(filename)

    data = None
    try:
        with open(filename, 'rt') as file:
            data = json.loads(file.read())
    except FileNotFoundError:
        print('Downloading car dictionary...')
        url = 'https://declarator.org/media/dumps/carbrand.json'
        urllib.request.urlretrieve(url, filename, progress_hook)
        print('\nDone.')
        data = get_cars(filename)

    gc.collect()

    return data


def create_mapping(entity_from, entity_to, field_from, field_to, as_set=False, filename=None):
    if filename == None:
        filename = entity_from + '_' + field_from + \
            '2' + entity_to + '_' + field_to
        if as_set == True:
            filename += '_set'
        filename += '.json'

    json_data = get_json()

    mapping = defaultdict(int)
    if as_set == True:
        mapping = defaultdict(list)

    for entry in json_data:
        e_from = entry['main'][entity_from]
        e_to = entry['main'][entity_to]
        if as_set == True:
            if not (e_to[field_to] in mapping[e_from[field_from]]):
                mapping[e_from[field_from]].append(e_to[field_to])
        else:
            mapping[e_from[field_from]] = e_to[field_to]

    with open(filename, 'wt') as file:
        json.dump(mapping, file, ensure_ascii=False)


def get_mapping(entity_from, entity_to, field_from, field_to, as_set=False, filename=None, update=False):
    if filename == None:
        filename = entity_from + '_' + field_from + \
            '2' + entity_to + '_' + field_to
        if as_set == True:
            filename += '_set'
        filename += '.json'

    if update == True:
        os.remove(filename)

    data = None
    try:
        with open(filename, 'rt') as file:
            data = json.loads(file.read())
    except FileNotFoundError:
        create_mapping(entity_from, entity_to, field_from,
                       field_to, as_set, filename)
        data = get_mapping(entity_from, entity_to,
                           field_from, field_to, as_set, filename)

    return data
