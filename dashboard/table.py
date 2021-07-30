import time
import re
from copy import deepcopy

from copy import deepcopy
from tinydb import TinyDB, where, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from sem.logging import process_logs, filter_logs

class Table(object):
    def __init__(self, log_path):
        db, data_dir = process_logs(log_path)
        # pass_data = filter_logs(db, time_end=0)
        data = db.table('logs').all()
        # print(filter_logs(db, time_end=0))
        self.cardinality = len(data)
        self.cardinality_filtered = len(data)
        self.db = db
        self.data = data
        self.columns = ['time', 'context', 'extended_context', 'component', 'function', 'arguments', 'severity_class', 'message']
        self.col_search = ['extended_context', 'component', 'argument', 'message']
        self.filter_request_values = None
        self.unique_context = set(ctx['context'] for ctx in data)
        self.unique_func = set(fun['function'] for fun in data)
        self.unique_component = set(comp["component"] for comp in data)

    def set_request(self, request):
        # print(self.filter_request_values)
        self.request_values = request.values
        # print('values')
        # print(self.request_values)
        # print(self.filter_request_values)

    def build_datatable(self):
        data = self._filter_logs()
        data = self._custom_filter(data)
        self.cardinality_filtered = len(data)
        data = self._custom_sort(data)
        data = self._custom_paging(data)
        # print('tt')
        # print(len(data))
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

        # print('hi')
        # print(request.values)
        # print(self.filter_request_values)
        # print('time')
        # print(float(self.filter_request_values['time_begin'][0]))
        # print(type(float(self.filter_request_values['time_begin'][0])))

    def get_unique_values(self, request):
        return{
                'context': list(self.unique_context),
                'function': list(self.unique_func),
                'component': list(self.unique_component)
              }

    def _filter_logs(self):
        if self.filter_request_values is not None:
            return filter_logs(self.db, severity_class=self.filter_request_values['severity_class'], context = self.filter_request_values['context'], function=self.filter_request_values['func'], time_begin=self.filter_request_values['time_begin'], time_end=self.filter_request_values['time_end'])
        else:
            return self.data
