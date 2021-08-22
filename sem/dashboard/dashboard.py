import re
import numpy as np

from copy import deepcopy
from tinydb import TinyDB, where, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from sem.logging import process_logs, filter_logs
from bisect import bisect_left, bisect_right


class dict_list_index_get_member(object):
    def __init__(self, dict_list, member):
        self.dict_list = dict_list
        self.member = member

    def __getitem__(self, index):
        return self.dict_list[index][self.member]

    def __len__(self):
        return self.dict_list.__len__()


class Dashboard(object):
    def __init__(self):
        self.columns = ['time', 'context', 'extended_context', 'component', 'function', 'arguments', 'severity_class', 'message']
        self.col_search = ['extended_context', 'arguments', 'message']
        self.log_class = ['ERROR', 'WARN', 'DEBUG', 'INFO', 'FUNCTION', 'LOGIC']
        self.filter_request_values = None

    def set_log_path(self, log_path):
        db, data_dir = process_logs(log_path)
        data = db.table('logs').all()
        self.cardinality = len(data)
        self.cardinality_filtered = len(data)
        self.db = db
        self.data = data
        self.old_filter_data = None
        self.unique_context = set(ctx['context'] for ctx in data)
        self.unique_func = set(fun['function'] for fun in data)
        self.unique_component = set(comp["component"] for comp in data)

    def set_request(self, request):
        self.request_values = request.values

    def getTotalTime(self):
        return self.data[-1]['time']

    def get_index_in_filtered_data(self, idx):
        if self.old_filter_data is not None:
            actual_index = bisect_left(dict_list_index_get_member(self.old_filter_data, 'index'), idx)
        else:
            actual_index = bisect_left(dict_list_index_get_member(self.data, 'index'), idx)

        return actual_index

    def jitter_logs(self, orig_data):
        unique_time = list(set([data['time'] for data in orig_data]))
        time_column = dict_list_index_get_member(orig_data, 'time')
        for timestamp in unique_time:
            un_t = orig_data[bisect_left(time_column, timestamp):bisect_right(time_column, timestamp)]
            for ctx in {i['context'] for i in un_t}:
                data = [item for item in un_t if item['context'] == ctx]
                if len(data) > 1:
                    offsets = np.linspace(-0.2, 0.2, len(data))
                    for idx, unique_context_item in enumerate(data):
                        unique_context_item['jitter_context'] = str(float(unique_context_item['context']) + offsets[idx])
                else:
                    data[0]['jitter_context'] = data[0]['context']

    def buildchart(self):
        orig_data = self._filter_logs()
        self.jitter_logs(orig_data)
        self.old_filter_data = orig_data
        return orig_data

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


    def get_metadata(self):
        return{
                'context': list(self.unique_context),
                'function': list(self.unique_func),
                'component': list(self.unique_component),
                'search_column': list(self.col_search),
                'all_columns': list(self.columns),
                'log_class': list(self.log_class)
                }

    def set_search_columns(self, request):
        if request.values.__contains__('search_column'):
            self.col_search = request.values.to_dict(flat=False)['search_column']
        else:
            self.col_search = []

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
                    component[comp] = self.log_class
                return filter_logs(self.db, context=self.filter_request_values['context'], function=self.filter_request_values['func'], time_begin=self.filter_request_values['time_begin'], time_end=self.filter_request_values['time_end'], components=component)
            else:
                return filter_logs(self.db, severity_class=self.filter_request_values['severity_class'], context=self.filter_request_values['context'], function=self.filter_request_values['func'], time_begin=self.filter_request_values['time_begin'], time_end=self.filter_request_values['time_end'])
        else:
            return self.data
