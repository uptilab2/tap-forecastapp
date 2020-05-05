#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import json
import datetime
import requests
import singer

from singer import Transformer, utils, metadata
from singer.catalog import Catalog, CatalogEntry
from singer.schema import Schema
from datetime import timedelta, date

REQUIRED_CONFIG_KEYS = ['start_date', 'apikey']
LOGGER = singer.get_logger()
SESSION = requests.Session()

BASE_API_URL = 'https://api.forecast.it/api/v1/'

CONFIG = {}
STATE = {}
AUTH = {}


def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        path)


def load_schemas():
    """ Load schemas from schemas folder """

    schemas = {}
    for filename in os.listdir(get_abs_path('schemas')):
        path = get_abs_path('schemas') + '/' + filename
        file_raw = filename.replace('.json', '')
        with open(path) as file:
            schemas[file_raw] = Schema.from_dict(json.load(file))
    return schemas


def discover():
    raw_schemas = load_schemas()
    streams = []
    for (stream_id, schema) in raw_schemas.items():

        # TODO: populate any metadata and stream's key properties here..

        stream_metadata = []
        key_properties = []
        streams.append(CatalogEntry(
            tap_stream_id=stream_id,
            stream=stream_id,
            schema=schema,
            key_properties=key_properties,
            metadata=stream_metadata,
            replication_key=None,
            is_view=None,
            database=None,
            table=None,
            row_count=None,
            stream_alias=None,
            replication_method=None,
            ))

    return Catalog(streams)


def request(url, params=None):
    params = params or {}
    headers = {'X-FORECAST-API-KEY': CONFIG['apikey']}
    req = requests.Request('GET', url=url, params=params,
                           headers=headers).prepare()

    LOGGER.info('GET {}'.format(req.url))
    resp = SESSION.send(req)
    resp.raise_for_status()
    return resp.json()


def get_url(endpoint):
    return BASE_API_URL + endpoint


def load_schema(entity):
    return utils.load_json(get_abs_path('schemas/{}.json'.format(entity)))


def get_start(key):
    if key not in STATE:
        STATE[key] = CONFIG['start_date']

    return STATE[key]


def sync_endpoint(
    schema_name,
    endpoint=None,
    path=None,
    special_field_name=None,
    special_field_value=None,
    keys=None,
    object_to_id=None,
    parameter_for_updated=None
    ):
    schema = load_schema(schema_name)
    bookmark_property = 'updated_at'
    LOGGER.info('Loading ' + schema_name)
    if keys is None:
        keys = ['id']
    singer.write_schema(schema_name, schema, keys,
                        bookmark_properties=[bookmark_property])

    start = get_start(schema_name)
    start_dt = datetime.datetime.strptime(start,
                    '%Y-%m-%dT%H:%M:%S.%fZ')
    updated_since = start_dt.strftime("%Y%m%dT%H%M%S")
    LOGGER.info('updated_since ' + updated_since)
    with Transformer() as transformer:
        url = get_url(endpoint or schema_name)
        url = endpoint or url
        if parameter_for_updated is not None:
            url = url + '?' + parameter_for_updated + '=' + updated_since
        response = request(url, None)
        LOGGER.info('URL :' + url)
        if schema_name is 'project_financials':
            response = [response]

        time_extracted = utils.now()

        for row in response:

            if special_field_name is not None:
                row[special_field_name] = special_field_value

            if object_to_id is not None:
                for key in object_to_id:
                    if row[key] is not None:
                        row[key + '_id'] = row[key]['id']
                    else:
                        row[key + '_id'] = None

            item = transformer.transform(row, schema)

            if not bookmark_property in item:
                item[bookmark_property] = \
                    datetime.datetime.now().strftime('%Y-%m-%d') \
                    + 'T00:00:00.00Z'
			
            if  datetime.datetime.strptime(item[bookmark_property],'%Y-%m-%dT%H:%M:%S.%fZ') >= start_dt:
                singer.write_record(schema_name, item,
                                    time_extracted=time_extracted)

                utils.update_state(STATE, schema_name,
                                   item[bookmark_property])
    singer.write_state(STATE)


def sync_allocations(
    schema_name,
    endpoint=None,
    path=None,
    special_field_name=None,
    special_field_value=None,
    keys=None,
    object_to_id=None,
    ):
    schema = load_schema(schema_name)
    bookmark_property = 'updated_at'
    LOGGER.info('Loading ' + schema_name)
    if keys is None:
        keys = ['id']
    singer.write_schema(schema_name, schema, keys,
                        bookmark_properties=[bookmark_property])

    start = get_start(schema_name)
    weekDays = [
            'monday',
            'tuesday',
            'wednesday',
            'thursday',
            'friday',
            'saturday',
            'sunday',
            ]
    with Transformer() as transformer:
        url = get_url(endpoint or schema_name)
        url = endpoint or url

        response = request(url, None)
        

        time_extracted = utils.now()

        for row in response:

             # add here logic

            date = datetime.datetime.strptime(row['start_date'],
                    '%Y-%m-%d')
            LOGGER.info("Project" + str(row['project']) + "-" + str(row['person']))
            end_date = datetime.datetime.strptime(row['end_date'],
                    '%Y-%m-%d')
            
            newRow = {}
            #LOGGER.info("ID:"  + str(row['id']))
            #LOGGER.info("Date :  "  + date.strftime('%Y%m%d'))

            while date <= end_date:
                #LOGGER.info('Date :  ' + str(date.weekday()) + 'weekday'
                #             + weekDays[date.weekday()])
                #LOGGER.info(row['project'])
                #LOGGER.info(row[weekDays[date.weekday()]])
                #LOGGER.info(str(date.strftime('%Y-%m-%d')))
                #if row['id'] = 72051:
                #    LOGGER.info(row['project'])
                #    LOGGER.info(row['person'])
                #    LOGGER.info(str(date.strftime('%Y-%m-%d')))
                #    LOGGER.info(str(end_date.strftime('%Y-%m-%d')))
                    
                             
                newRow['allocation'] = row[weekDays[date.weekday()]]
                if not newRow['allocation'] > 0:
                    date = date + timedelta(days=1)
                    continue
                newRow['project'] = row['project']
                newRow['non_project_time'] = row['non_project_time']
                newRow['connected_project'] = row['connected_project']
                newRow['person'] = row['person']
                newRow['project'] = row['project']
                newRow['date'] = date.strftime('%Y-%m-%d')
                newRow['notes'] = row['notes']
                newRow['created_by'] = row['created_by']
                newRow['updated_by'] = row['updated_by']
                newRow['created_at'] = row['created_at']
                newRow['updated_at'] = row['updated_at']
                newRow['id'] = str(row['id']) \
                    + str(date.strftime('%Y%m%d'))

                date = date + timedelta(days=1)

                item = transformer.transform(newRow, schema)

                if not bookmark_property in item:
                    item[bookmark_property] = \
                        datetime.datetime.now().strftime('%Y-%m-%d') \
                        + 'T00:00:00Z'

                if bookmark_property in item \
                    and item[bookmark_property] >= start:
                    singer.write_record(schema_name, item,
                            time_extracted=time_extracted)

                    utils.update_state(STATE, schema_name,
                            item[bookmark_property])
                else:
                    singer.write_record(schema_name, item,
                            time_extracted=time_extracted)

                    # take any additional actions required for the currently loaded endpoint

                    utils.update_state(STATE, schema_name,
                            item[bookmark_property])
        singer.write_state(STATE)

def sync_project(  # pylint: disable=too-many-arguments
    schema_name,
    endpoint=None,
    path=None,
    special_field_name=None,
    special_field_value=None,
    date_fields=None,
    with_updated_since=True,
    for_each_handler=None,
    map_handler=None,
    object_to_id=None,
    ):
    schema = load_schema(schema_name)
    bookmark_property = 'updated_at'
    LOGGER.info('Loading ' + schema_name)
    singer.write_schema(schema_name, schema, ['id'],
                        bookmark_properties=[bookmark_property])

    start = get_start(schema_name)

    with Transformer() as transformer:
        url = get_url(endpoint or schema_name)
        url = endpoint or url

        response = request(url, None)

        for row in response:

            item = transformer.transform(row, schema)

            time_extracted = utils.now()

            # find related

            sync_endpoint('expense_items', BASE_API_URL + 'projects/'
                          + str(row['id']) + '/expense_items', None,
                          'project_id', str(row['id']))
            sync_endpoint('invoices', BASE_API_URL + 'projects/'
                          + str(row['id']) + '/invoices', None,
                          'project_id', str(row['id']))
            sync_endpoint('milestones', BASE_API_URL + 'projects/'
                          + str(row['id']) + '/milestones', None,
                          'project_id', str(row['id']))
            sync_endpoint(
                'project_team',
                BASE_API_URL + 'projects/' + str(row['id']) + '/team',
                None,
                'project_id',
                str(row['id']),
                ['person_id', 'project_id'],
                )
            sync_endpoint('sprints', BASE_API_URL + 'projects/'
                          + str(row['id']) + '/sprints', None,
                          'project_id', str(row['id']))
            sync_endpoint('workflow_columns', BASE_API_URL + 'projects/'
                           + str(row['id']) + '/workflow_columns',
                          None, 'project_id', str(row['id']))
            sync_endpoint(
                'project_financials',
                BASE_API_URL + 'projects/' + str(row['id'])
                    + '/financials',
                None,
                None,
                None,
                ['project_id'],
                )

            if bookmark_property in item and item[bookmark_property] \
                >= start:
                singer.write_record(schema_name, item,
                                    time_extracted=time_extracted)

                utils.update_state(STATE, schema_name,
                                   item[bookmark_property])
    singer.write_state(STATE)


def sync_rate_cards(  # pylint: disable=too-many-arguments
    schema_name,
    endpoint=None,
    path=None,
    special_field_name=None,
    special_field_value=None,
    date_fields=None,
    with_updated_since=True,
    for_each_handler=None,
    map_handler=None,
    object_to_id=None,
    ):
    schema = load_schema(schema_name)
    bookmark_property = 'updated_at'
    LOGGER.info('Loading ' + schema_name)
    singer.write_schema(schema_name, schema, ['id'],
                        bookmark_properties=[bookmark_property])

    start = get_start(schema_name)

    with Transformer() as transformer:
        url = get_url(endpoint or schema_name)
        url = endpoint or url
        response = request(url, None)

        time_extracted = utils.now()

        for row in response:
            if map_handler is not None:
                row = map_handler(row)

            if object_to_id is not None:
                for key in object_to_id:
                    if row[key] is not None:
                        row[key + '_id'] = row[key]['id']
                    else:
                        row[key + '_id'] = None

            item = transformer.transform(row, schema)
            if not bookmark_property in item:
                item[bookmark_property] = \
                    datetime.datetime.now().strftime('%Y-%m-%d') \
                    + 'T00:00:00Z'

            # find expenses

            sync_endpoint(
                'rate_cards_rates',
                BASE_API_URL + 'rate_cards/' + str(row['id']) + '/rates'
                    ,
                None,
                'rate_card_id',
                str(row['id']),
                ['rate_card_id', 'role'],
                )

            singer.write_record(schema_name, item,
                                time_extracted=time_extracted)

            # take any additional actions required for the currently loaded endpoint

            utils.update_state(STATE, schema_name,
                               item[bookmark_property])
    singer.write_state(STATE)


def sync(config, state, catalog):
    """ Sync data from tap source """

    # Loop over selected streams in catalog

    LOGGER.info('Starting sync')

    sync_project("projects")
    sync_endpoint("allocations")

    sync_allocations('allocations_perday', BASE_API_URL + 'allocations')

    sync_endpoint("tasks","https://api.forecast.it/api/v2/tasks",None,None,None,None,None,'updated_after')
    sync_endpoint("clients")
    sync_endpoint("connected_projects")
    sync_endpoint("holiday_calendar_entries")
    sync_endpoint("holiday_calendars")
    sync_endpoint("labels")
    sync_endpoint("non_project_time")
    sync_endpoint("persons")
    sync_endpoint("person_cost_periods")
    sync_rate_cards("rate_cards")
     #sync_endpoint("repeating_tasks")
    sync_endpoint("roles")
    sync_endpoint("time_registrations","https://api.forecast.it/api/v3/time_registrations",None,None,None,None,None,'updated_after')

    return


@utils.handle_top_exception(LOGGER)
def main():

    # Parse command line arguments

    args = utils.parse_args(REQUIRED_CONFIG_KEYS)
    CONFIG.update(args.config)
    STATE.update(args.state)
    # If discover flag was passed, run discovery mode and dump output to stdout

    if args.discover:
        catalog = discover()
        catalog.dump()
    else:

    # Otherwise run in sync mode

        if args.catalog:
            catalog = args.catalog
        else:
            catalog = discover()
        sync(args.config, args.state, catalog)

if __name__ == '__main__':
    main()
