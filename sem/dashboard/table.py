import time
import re
import numpy as np

from copy import deepcopy
from copy import deepcopy
from tinydb import TinyDB, where, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from sem.logging import process_logs, filter_logs


class Table(object):
    def __init__(self):
        self.columns = ['time', 'context', 'extended_context', 'component', 'function', 'arguments', 'severity_class', 'message']
        self.col_search = ['extended_context', 'component', 'arguments', 'message']
        self.filter_request_values = None

    def set_log_path(self, log_path):
        db, data_dir = process_logs(log_path)
        # pass_data = filter_logs(db, time_end=0)
        data = db.table('logs').all()
        for idx, entry in enumerate(data):
            entry['index'] = idx
        # print(filter_logs(db, time_end=0))
        self.cardinality = len(data)
        self.cardinality_filtered = len(data)
        self.db = db
        self.data = data
        self.unique_context = set(ctx['context'] for ctx in data)
        self.unique_func = set(fun['function'] for fun in data)
        self.unique_component = set(comp["component"] for comp in data)

    def set_request(self, request):
        # print(self.filter_request_values)
        self.request_values = request.values
        # print('values')
        # print(self.request_values)
        # print(self.filter_request_values)

    def getTotalTime(self):
        return self.data[-1]['time']

    def buildchart(self):
        # Jitter Logs
        orig_data = deepcopy(self._filter_logs())
        orig_data = orig_data[0:1000]
        unique_time = list(set([data['time'] for data in orig_data]))
        # Trimed to make it work temporarily
        # unique_time = unique_time[0:20]
        ret_data = []
        for timestamp in unique_time:
            un_t = [i for i in orig_data if i['time'] == timestamp]
            for ctx in {i['context'] for i in un_t}:
                data = [item for item in un_t if item['context'] == ctx ]
                if len(data) > 1:
                    offsets = np.linspace(-0.2, 0.2, len(data))
                    for idx, unique_context_item in enumerate(data):
                        unique_context_item['context'] = str(float(unique_context_item['context']) + offsets[idx])
            ret_data += un_t
        # data = deepcopy(self.data)
        # for unique_time in {i['time'] for i in data}:
        #     # print("Unique time: %s" % unique_time)
        #     unique_time_items = [item for item in data if item['time'] ==
        #                         unique_time]
        #     for unique_context in {i['context'] for i in unique_time_items}:
        #         # print("Unique context: %s" % unique_context)
        #         unique_context_items = [item for item in unique_time_items if
        #                                 item['context'] == unique_context]
        #         if len(unique_context_items) > 1:
        #             offsets = np.linspace(-0.2, 0.2, len(unique_context_items))
        #             print(offsets)
        #             for idx, unique_context_item in enumerate(unique_context_items):
        #                 unique_context_item['context'] = str(float(unique_context_item['context']) + offsets[idx])
        return sorted(ret_data, key=lambda k: k['time'])

    def build_datatable(self):
        data = self._filter_logs()
        data = self._custom_filter(data)
        self.cardinality_filtered = len(data)
        data = self._custom_sort(data)
        data = self._custom_paging(data)
        output = {}
        output['sEcho'] = str(int(self.request_values['sEcho']))
        output['iTotalRecords'] = str(self.cardinality)
        output['iTotalDisplayRecords'] = str(self.cardinality_filtered)
        output['data'] = data
        return output

    def _custom_paging(self, data):
        if self.request_values['iDisplayStart'] != "" and int(self.request_values['iDisplayLength']) != -1:

            start = int(self.request_values['iDisplayStart'])
            length = int(self.request_values['iDisplayLength'])
            if len(data) <= length:
                return data[start:]
            else:
                limit = start + length - len(data)
                if limit < 0:
                    return data[start:limit]
                else:
                    return data[start:]
        # if int(self.request_values['iDisplayLength']) == -1:
        #     print(len(data))
        #     return data[0:200000]

    def _custom_filter(self, data):
        def check_row(row):
            for i in range(len(self.col_search)):
                value = row[self.col_search[i]]
                regex = self.request_values['sSearch']
                if re.compile(regex).search(str(value)):
                    return True
            return False

        if self.request_values.get('sSearch', ""):
            return [row for row in data if check_row(row)]
        else:
            return data

    def _custom_sort(self, data):

        if (self.request_values['iSortCol_0'] != "") and (int(self.request_values['iSortingCols']) > 0):
            for i in range(0, int(self.request_values['iSortingCols'])):
                column_number = int(self.request_values['iSortCol_' + str(i)])
                column_name = self.columns[column_number]
                sort_direction = self.request_values['sSortDir_' + str(i)]
                # print(len(data))
                data = sorted(data,
                              key=lambda x: x[column_name],
                              reverse=True if sort_direction == 'desc' else False)
            return data
        else:
            return data

    def set_filter_request(self, request):
        self.filter_request_values = deepcopy(request.values.to_dict(flat=False))
        if 'severity_class' not in self.filter_request_values:
            self.filter_request_values['severity_class'] = None

        if 'context' not in self.filter_request_values:
            self.filter_request_values['context'] = None

        if 'func' not in self.filter_request_values:
            self.filter_request_values['func'] = None

        if 'component' not in self.filter_request_values:
            self.filter_request_values['component'] = None

        if self.filter_request_values['time_begin'][0] == '':
            self.filter_request_values['time_begin'] = None
        else:
            self.filter_request_values['time_begin'] = self.filter_request_values['time_begin'][0]

        if self.filter_request_values['time_end'][0] == '':
            self.filter_request_values['time_end'] = None
        else:
            self.filter_request_values['time_end'] = self.filter_request_values['time_end'][0]

        # print('hi')
        # print(request.values)
        # print(self.filter_request_values)
        # print('time')
        # print(float(self.filter_request_values['time_begin'][0]))
        # print(type(float(self.filter_request_values['time_begin'][0])))

    def get_unique_values(self):
        return{
                'context': list(self.unique_context),
                'function': list(self.unique_func),
                'component': list(self.unique_component)
              }

    def _filter_logs(self):
        if self.filter_request_values is not None:
            component = None
            if self.filter_request_values['component'] is not None and self.filter_request_values['severity_class'] is not None:
                component = {}
                for comp in self.filter_request_values['component']:
                    component[comp] = self.filter_request_values['severity_class']
                return filter_logs(self.db, context=self.filter_request_values['context'], function=self.filter_request_values['func'], time_begin=self.filter_request_values['time_begin'], time_end=self.filter_request_values['time_end'], components=component)
            elif self.filter_request_values['component'] is not None and self.filter_request_values['severity_class'] is None:
                component = {}
                for comp in self.filter_request_values['component']:
                    component[comp] = ['ERROR', 'WARN', 'DEBUG', 'INFO', 'FUNCTION', 'LOGIC']
                return filter_logs(self.db, context=self.filter_request_values['context'], function=self.filter_request_values['func'], time_begin=self.filter_request_values['time_begin'], time_end=self.filter_request_values['time_end'], components=component)
            else:
                return filter_logs(self.db, severity_class=self.filter_request_values['severity_class'], context=self.filter_request_values['context'], function=self.filter_request_values['func'], time_begin=self.filter_request_values['time_begin'], time_end=self.filter_request_values['time_end'])
        else:
            return self.data
