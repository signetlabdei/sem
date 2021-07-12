from sem.utils import filter_logs, insert_logs, parse_logs, wipe_results
import sem
from math import log
from sem import list_param_combinations, automatic_parser, stdout_automatic_parser, parse_log_components
import json
import numpy as np
import pytest
import os
import time
from operator import getitem

from tinydb import TinyDB
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware


def test_list_param_combinations():
    # Two possible combinations
    d1 = {'a': [1, 2]}
    assert set(map(lambda x: getitem(x, 'a'),
                   list_param_combinations(d1))) == set([1, 2])

    # Two possible combinations with two specified values
    d2 = {'b': [3], 'c': [4, 5]}
    assert set(map(lambda x: getitem(x, 'b'),
                   list_param_combinations(d2))) == set([3, 3])
    assert set(map(lambda x: getitem(x, 'c'),
                   list_param_combinations(d2))) == set([4, 5])

    # Four combinations with two specified values
    d3 = {'d': [6, 7], 'e': [8, 9]}
    assert sorted(map(lambda x: json.dumps(x, sort_keys=True),
                      list_param_combinations(d3))) == sorted(
                          map(lambda x: json.dumps(x, sort_keys=True),
                              [{'d': 6, 'e': 8}, {'d': 7, 'e': 8},
                               {'d': 6, 'e': 9}, {'d': 7, 'e': 9}]))

    params = {
        'a': [1],
        'b': [1, 2, 3],
    }
    params_more = {
        'a': [3],
        'b': [1, 2, 3],
    }
    params_same_as_above = {
        'a': [1, 3],
        'b': [1, 2, 3],
    }
    assert (sorted(map(lambda x: json.dumps(x, sort_keys=True),
                       list_param_combinations(params_same_as_above)))
            ==
            sorted(map(lambda x: json.dumps(x, sort_keys=True),
                       list_param_combinations([params, params_more]))))

    params_with_lambda = {
        'a': [1, 3],
        'b': lambda p: [10 * p['a']]
    }
    assert (sorted(map(lambda x: json.dumps(x, sort_keys=True),
                       list_param_combinations(params_with_lambda)))
            ==
            sorted(map(lambda x: json.dumps(x, sort_keys=True),
                       [{'a': 1, 'b': 10}, {'a': 3, 'b': 30}])))

    params_with_lambda_returning_list = {
        'a': [1, 3],
        'b': lambda p: list(range(p['a'])),
    }
    assert (sorted(map(lambda x: json.dumps(x, sort_keys=True),
                       list_param_combinations(params_with_lambda_returning_list)))
            ==
            sorted(map(lambda x: json.dumps(x, sort_keys=True),
                       [{'a': 1, 'b': 0}, {'a': 3, 'b': 0},
                        {'a': 3, 'b': 1}, {'a': 3, 'b': 2}])))

    params_with_two_lambdas = {
        'a': [1, 3],
        'b': lambda p: list(range(p['a'])),
        'c': lambda p: [10 * p['b']]
    }
    assert (sorted(map(lambda x: json.dumps(x, sort_keys=True),
                       list_param_combinations(params_with_two_lambdas)))
            ==
            sorted(map(lambda x: json.dumps(x, sort_keys=True),
                       [{'a': 1, 'b': 0, 'c': 0}, {'a': 3, 'b': 0, 'c': 0},
                        {'a': 3, 'b': 1, 'c': 10}, {'a': 3, 'b': 2, 'c': 20}])))


def test_stdout_automatic_parser(result):
    # Create a dummy result
    result['output'] = {}
    result['output']['stderr'] = ''
    result['output']['stdout'] = '1 2 3 4 5\n6 7 8 9 10'

    parsed = stdout_automatic_parser(result)

    assert np.all(parsed == [[1, 2, 3, 4, 5],
                             [6, 7, 8, 9, 10]])


def test_automatic_parser(result):
    # Create a dummy result
    result['output'] = {}
    result['output']['stderr'] = ''
    result['output']['stdout'] = '1 2 3 4 5\n6 7 8 9 10'

    parsed = automatic_parser(result)

    assert np.all(parsed['stdout'] == [[1, 2, 3, 4, 5],
                                       [6, 7, 8, 9, 10]])
    assert parsed['stderr'] == []


def test_parse_log_components(ns_3_compiled_debug, config):
    log_components = {
                'component1': 'info|prefix_level',
                'component2': 'level_debug|info',
                'component3': 'all|prefix_all',
                'component4': '**',
                'component5': '*|info',
                'component6': 'info|*',
                'component7': 'prefix_all'
            }

    new_components = parse_log_components(log_components=log_components)

    assert new_components == {
        'component1': 'info',
        'component2': 'error|warn|debug|info',
        'component3': 'error|warn|debug|info|function|logic',
        'component4': 'error|warn|debug|info|function|logic',
        'component5': 'error|warn|debug|info|function|logic',
        'component6': 'info',
        'component7': ''
    }

    log_components = {
        'component1': 'info|err'
    }

    with pytest.raises(ValueError):
        new_components = parse_log_components(log_components=log_components)

    new_campaign = sem.CampaignManager.new(ns_3_compiled_debug,
                                           'logging-ns3-script',
                                           config['campaign_dir'],
                                           overwrite=True,
                                           optimized=False)

    log_components = {
        '*': 'info',
        'Simulator': 'level_info'
    }

    with pytest.raises(ValueError):
        new_components = parse_log_components(log_components=log_components)

    ns3_log_components = new_campaign.runner.get_available_log_components()

    new_components = parse_log_components(log_components=log_components,
                                         ns3_log_components=ns3_log_components)

    assert new_components['Simulator'] == 'error|warn|debug|info'

    log_components = {
        'NonExistentLogComponent': 'info'
    }

    with pytest.raises(ValueError):
        new_components = parse_log_components(log_components=log_components,
                                             ns3_log_components=ns3_log_components)

def test_parse_logs():
    data_dir = os.path.join(os.curdir, 'tests', str(time.strftime("%Y-%m-%d::%H-%M-%S")) + ':test_logs.json')

    log_ls = ['+0.000000000s -1 [mac=00:00:00:00:00:00] FrameExchangeManager:SetWifiMac(0x5576595683e0, 0x557659603820)\n',
              '+0.045510017s 1 [mac=00:00:00:00:00:01] FrameExchangeManager:RxStartIndication(0x5576595683e0, "PSDU reception started for ", +76us, " (txVector: ", txpwrlvl: 17 preamble: LONG channel width: 20 GI: 800 NTx: 97 Ness: 0 MPDU aggregation: 0 STBC: 0 FEC coding: BCC mode: OfdmRate6Mbps Nss: 1, ")")\n',
              '+0.000000000s -1 WifiPhy:WifiPhy(0x557659571bd0)\n',
              '+0.000000000s -1 WifiPhy:SetChannelNumber(): [DEBUG] Saving channel number configuration for initialization \n',
              '+0.506390387s 1 [mac=00:00:00:00:00:01] FrameExchangeManager:StartTransmission(): [DEBUG] MPDU payload size=36, to=00:00:00:00:00:02, seq=16 \n',
              'WifiPhy:AddStaticPhyEntity(HR/DSSS) \n',
              '+0.000000000s -1 WifiPhy:SetChannelNumber(): [DEBUG] ()[]./-=\n',
              '+0.000000000s -1 WifiPhy:SetChannelNumber() \n',
              '+0.000000000s -1 WifiPhy:SetChannelNumber): [DEBUG] Saving channel number configuration for initialization \n',
              '+0.000000000s -1 WifiPhy:SetChannelNumber(): DEBUG] Saving channel number configuration for initialization \n',
              '+0.000000000s WifiPhy:SetChannelNumber(): [DEBUG] Saving channel number configuration for initialization \n']
    with open(data_dir, "w") as f:
        f.writelines(log_ls)

    parse_list = parse_logs(data_dir)

    expected_list = [
        {
            'Time': 0.000000000,
            'Context': '-1',
            'Extended_context': 'mac=00:00:00:00:00:00',
            'Component': 'FrameExchangeManager',
            'Function': 'SetWifiMac',
            'Arguments': '0x5576595683e0, 0x557659603820',
            'Severity_class': 'FUNCTION',
            'Message': ''
        },
        {
            'Time': 0.045510017,
            'Context': '1',
            'Extended_context': 'mac=00:00:00:00:00:01',
            'Component': 'FrameExchangeManager',
            'Function': 'RxStartIndication',
            'Arguments': '0x5576595683e0, "PSDU reception started for ", +76us, " (txVector: ", txpwrlvl: 17 preamble: LONG channel width: 20 GI: 800 NTx: 97 Ness: 0 MPDU aggregation: 0 STBC: 0 FEC coding: BCC mode: OfdmRate6Mbps Nss: 1, ")"',
            'Severity_class': 'FUNCTION',
            'Message': ''
        },
        {
            'Time': 0.000000000,
            'Context': '-1',
            'Extended_context': None,
            'Component': 'WifiPhy',
            'Function': 'WifiPhy',
            'Arguments': '0x557659571bd0',
            'Severity_class': 'FUNCTION',
            'Message': ''
        },
        {
            'Time': 0.000000000,
            'Context': '-1',
            'Extended_context': None,
            'Component': 'WifiPhy',
            'Function': 'SetChannelNumber',
            'Arguments': '',
            'Severity_class': 'DEBUG',
            'Message': 'Saving channel number configuration for initialization'
        },
        {
            'Time': 0.506390387,
            'Context': '1',
            'Extended_context': 'mac=00:00:00:00:00:01',
            'Component': 'FrameExchangeManager',
            'Function': 'StartTransmission',
            'Arguments': '',
            'Severity_class': 'DEBUG',
            'Message': 'MPDU payload size=36, to=00:00:00:00:00:02, seq=16'
        },
        {
            'Time': 0.000000000,
            'Context': '-1',
            'Extended_context': None,
            'Component': 'WifiPhy',
            'Function': 'SetChannelNumber',
            'Arguments': '',
            'Severity_class': 'DEBUG',
            'Message': '()[]./-='
        }
    ]

    assert len(parse_list) == 6
    assert all([actual == expected for actual, expected in zip(parse_list, expected_list)])

    os.remove(data_dir)


def test_filters():
    db_dir = os.path.join(os.curdir, 'tests', str(time.strftime("%Y-%m-%d::%H-%M-%S")) + ':test_logs.json')
    data_dir = os.path.join(os.curdir, 'tests', str(time.strftime("%Y-%m-%d::%H-%M-%S")) + ':test_logs')

    db = TinyDB(db_dir,
                storage=CachingMiddleware(JSONStorage))

    log_ls = ['+0.000000000s -1 [mac=00:00:00:00:00:00] FrameExchangeManager:SetWifiMac(0x5576595683e0, 0x557659603820)\n',
              '+0.045510017s 1 [mac=00:00:00:00:00:01] FrameExchangeManager:RxStartIndication(0x5576595683e0, "PSDU reception started for ", +76us, " (txVector: ", txpwrlvl: 17 preamble: LONG channel width: 20 GI: 800 NTx: 97 Ness: 0 MPDU aggregation: 0 STBC: 0 FEC coding: BCC mode: OfdmRate6Mbps Nss: 1, ")")\n',
              '+0.506390387s 1 [mac=00:00:00:00:00:01] FrameExchangeManager:StartTransmission(): [DEBUG] MPDU payload size=36, to=00:00:00:00:00:02, seq=16\n',
              '+2.999074264s 0 [mac=00:00:00:00:00:02] FrameExchangeManager:NotifyReceivedNormalAck(0x56239764d8c0, DATA, payloadSize=1456, to=00:00:00:00:00:01, seqN=2323, duration/ID=+44000ns, lifetime=+195539us, packet=0x56239786dd00)\n',
              '+0.000000000s -1 WifiPhy:WifiPhy(0x557659571bd0)\n',
              '+0.000000000s -1 WifiPhy:SetChannelNumber(): [DEBUG] Saving channel number configuration for initialization\n',
              '+0.000000000s -1 WifiPhy:SetChannelNumber(): [DEBUG] ()[]./-=\n',
              '+2.999825333s 1 WifiPhy:GetTxPowerForTransmission(): [INFO ] txPowerDbm=17 with txPowerDbmPerMhz=3.9897 over 20 MHz\n',
              '+2.999825333s 1 WifiPhy:GetTxPowerForTransmission(): [INFO ] txPowerDbm=17 after applying m_powerDensityLimit=100\n'
              ]

    with open(data_dir, "w") as f:
        f.writelines(log_ls)

    parse_list = parse_logs(data_dir)
    insert_logs(parse_list, db)

    filter_list = filter_logs(db, context=['1'])
    assert len(filter_list) == 4
    assert filter_list == [
        {'Time': 0.045510017,
         'Context': '1',
         'Extended_context': 'mac=00:00:00:00:00:01',
         'Component': 'FrameExchangeManager',
         'Function': 'RxStartIndication',
         'Arguments': '0x5576595683e0, "PSDU reception started for ", +76us, " (txVector: ", txpwrlvl: 17 preamble: LONG channel width: 20 GI: 800 NTx: 97 Ness: 0 MPDU aggregation: 0 STBC: 0 FEC coding: BCC mode: OfdmRate6Mbps Nss: 1, ")"',
         'Severity_class': 'FUNCTION',
         'Message': ''
         },
        {'Time': 0.506390387,
         'Context': '1',
         'Extended_context': 'mac=00:00:00:00:00:01',
         'Component': 'FrameExchangeManager',
         'Function': 'StartTransmission',
         'Arguments': '',
         'Severity_class': 'DEBUG',
         'Message': 'MPDU payload size=36, to=00:00:00:00:00:02, seq=16'
         },
        {'Time': 2.999825333,
         'Context': '1',
         'Extended_context': None,
         'Component': 'WifiPhy',
         'Function': 'GetTxPowerForTransmission',
         'Arguments': '',
         'Severity_class': 'INFO',
         'Message': 'txPowerDbm=17 with txPowerDbmPerMhz=3.9897 over 20 MHz'
         },
        {'Time': 2.999825333,
         'Context': '1',
         'Extended_context': None,
         'Component': 'WifiPhy',
         'Function': 'GetTxPowerForTransmission',
         'Arguments': '',
         'Severity_class': 'INFO',
         'Message': 'txPowerDbm=17 after applying m_powerDensityLimit=100'
         }
    ]

    filter_list = filter_logs(db, context=['1'], function='GetTxPowerForTransmission')
    assert len(filter_list) == 2
    assert filter_list == [
        {'Time': 2.999825333,
         'Context': '1',
         'Extended_context': None,
         'Component': 'WifiPhy',
         'Function': 'GetTxPowerForTransmission',
         'Arguments': '',
         'Severity_class': 'INFO',
         'Message': 'txPowerDbm=17 with txPowerDbmPerMhz=3.9897 over 20 MHz'
         },
        {'Time': 2.999825333,
         'Context': '1',
         'Extended_context': None,
         'Component': 'WifiPhy',
         'Function': 'GetTxPowerForTransmission',
         'Arguments': '',
         'Severity_class': 'INFO',
         'Message': 'txPowerDbm=17 after applying m_powerDensityLimit=100'
         }
    ]

    filter_list = filter_logs(db, context=['1'], sevirity_class=['info'])
    assert len(filter_list) == 2
    assert filter_list == [
        {'Time': 2.999825333,
         'Context': '1',
         'Extended_context': None,
         'Component': 'WifiPhy',
         'Function': 'GetTxPowerForTransmission',
         'Arguments': '',
         'Severity_class': 'INFO',
         'Message': 'txPowerDbm=17 with txPowerDbmPerMhz=3.9897 over 20 MHz'
         },
        {'Time': 2.999825333,
         'Context': '1',
         'Extended_context': None,
         'Component': 'WifiPhy',
         'Function': 'GetTxPowerForTransmission',
         'Arguments': '',
         'Severity_class': 'INFO',
         'Message': 'txPowerDbm=17 after applying m_powerDensityLimit=100'
         }
    ]

    filter_list = filter_logs(db, context=['1'], time_begin=0.6)
    assert len(filter_list) == 2
    assert filter_list == [
        {'Time': 2.999825333,
         'Context': '1',
         'Extended_context': None,
         'Component': 'WifiPhy',
         'Function': 'GetTxPowerForTransmission',
         'Arguments': '',
         'Severity_class': 'INFO',
         'Message': 'txPowerDbm=17 with txPowerDbmPerMhz=3.9897 over 20 MHz'
         },
        {'Time': 2.999825333,
         'Context': '1',
         'Extended_context': None,
         'Component': 'WifiPhy',
         'Function': 'GetTxPowerForTransmission',
         'Arguments': '',
         'Severity_class': 'INFO',
         'Message': 'txPowerDbm=17 after applying m_powerDensityLimit=100'
         }
    ]

    filter_list = filter_logs(db, context=['1'], time_end=0.5)
    assert len(filter_list) == 1
    assert filter_list == [
        {'Time': 0.045510017,
         'Context': '1',
         'Extended_context': 'mac=00:00:00:00:00:01',
         'Component': 'FrameExchangeManager',
         'Function': 'RxStartIndication',
         'Arguments': '0x5576595683e0, "PSDU reception started for ", +76us, " (txVector: ", txpwrlvl: 17 preamble: LONG channel width: 20 GI: 800 NTx: 97 Ness: 0 MPDU aggregation: 0 STBC: 0 FEC coding: BCC mode: OfdmRate6Mbps Nss: 1, ")"',
         'Severity_class': 'FUNCTION',
         'Message': ''
         }
    ]

    filter_list = filter_logs(db, sevirity_class='function')
    print(filter_list)
    assert len(filter_list) == 4
    assert filter_list == [
        {'Time': 0.0,
         'Context': '-1',
         'Extended_context': 'mac=00:00:00:00:00:00',
         'Component': 'FrameExchangeManager',
         'Function': 'SetWifiMac',
         'Arguments': '0x5576595683e0, 0x557659603820',
         'Severity_class': 'FUNCTION',
         'Message': ''
         },
        {'Time': 0.045510017,
         'Context': '1',
         'Extended_context': 'mac=00:00:00:00:00:01',
         'Component': 'FrameExchangeManager',
         'Function': 'RxStartIndication',
         'Arguments': '0x5576595683e0, "PSDU reception started for ", +76us, " (txVector: ", txpwrlvl: 17 preamble: LONG channel width: 20 GI: 800 NTx: 97 Ness: 0 MPDU aggregation: 0 STBC: 0 FEC coding: BCC mode: OfdmRate6Mbps Nss: 1, ")"',
         'Severity_class': 'FUNCTION',
         'Message': ''
         },
        {'Time': 2.999074264,
         'Context': '0',
         'Extended_context': 'mac=00:00:00:00:00:02',
         'Component': 'FrameExchangeManager',
         'Function': 'NotifyReceivedNormalAck',
         'Arguments': '0x56239764d8c0, DATA, payloadSize=1456, to=00:00:00:00:00:01, seqN=2323, duration/ID=+44000ns, lifetime=+195539us, packet=0x56239786dd00',
         'Severity_class': 'FUNCTION',
         'Message': ''
         },
        {'Time': 0.0,
         'Context': '-1',
         'Extended_context': None,
         'Component': 'WifiPhy',
         'Function': 'WifiPhy',
         'Arguments': '0x557659571bd0',
         'Severity_class': 'FUNCTION',
         'Message': ''
         }
    ]

    wipe_results(db, db_dir)
    os.remove(data_dir)
