from collections import defaultdict
import urllib.request
import json
import time
import sys
import os
import io
import gc


def default_filter(entry): return entry['main']['document_type']['id'] == 1


def get_json(filename='declarations.json', update=False):
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

    data = None
    try:
        with open(filename, 'rt') as file:
            data = json.loads(file.read())
    except FileNotFoundError:
        print('Downloading data...')
        url = 'https://declarator.org/media/dumps/declarations.json'
        urllib.request.urlretrieve(url, filename, progress_hook)
        print('Done.')
        data = get_json(filename)
    gc.collect()
    return data


def get_updated_json(filename='declarations.json'):
    os.remove(filename)  # Make sure that you have enough privileges
    return get_json(filename, update=True)


def filter_data(data, some_filter=default_filter):
    return filter(some_filter, data)


def create_list(entity, filename=None):
    if filename == None:
        filename = entity + '_list.json'

    json_data = get_json()
    json_data = filter_data(json_data)

    entries = defaultdict(str)
    for entry in json_data:
        e = entry['main'][entity]
        entries[e['id']] = e['name']

    with open(filename, 'wt') as file:
        json.dump(entries, file, ensure_ascii=False)


def get_list(entity, filename=None):
    if filename == None:
        filename = entity + '_list.json'

    data = None
    try:
        with open(filename, 'rt') as file:
            data = json.loads(file.read())
    except FileNotFoundError:
        create_list(entity, filename)
        data = get_list(entity, filename)
    return data
