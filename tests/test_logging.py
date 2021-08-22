import os
import time
import pytest

from tinydb import TinyDB
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from sem.logging import filter_logs, insert_logs, parse_logs, wipe_results

log_ls = ['+0.000000000s -1 [node -1] FrameExchangeManager:SetWifiMac(0x5576595683e0, 0x557659603820)\n',
          '+0.045510017s 1 [mac=00:00:00:00:00:01] FrameExchangeManager:RxStartIndication(0x5576595683e0, "PSDU reception started for ", +76us, " (txVector: ", txpwrlvl: 17 preamble: LONG channel width: 20 GI: 800 NTx: 97 Ness: 0 MPDU aggregation: 0 STBC: 0 FEC coding: BCC mode: OfdmRate6Mbps Nss: 1, ")")\n',
          '+0.000000000s -1 WifiPhy:SetChannelNumber(): [DEBUG] Saving channel number configuration for initialization \n',
          '+0.506390387s 1 [mac=00:00:00:00:00:01] FrameExchangeManager:StartTransmission(): [DEBUG] MPDU payload size=36, to=00:00:00:00:00:02, seq=16 \n',
          '+2.999074264s 0 [mac=00:00:00:00:00:02] FrameExchangeManager:NotifyReceivedNormalAck(0x56239764d8c0, DATA, payloadSize=1456, to=00:00:00:00:00:01, seqN=2323, duration/ID=+44000ns, lifetime=+195539us, packet=0x56239786dd00)\n',
          '+0.000000000s -1 WifiPhy:WifiPhy(0x557659571bd0)\n',
          '+0.000000000s -1 WifiPhy:SetChannelNumber(): [INFO  ] :()[]:./-=\n',
          '+2.999825333s 1 WifiPhy:GetTxPowerForTransmission(): [DEBUG ] txPowerDbm=17 with txPowerDbmPerMhz=3.9897 over 20 MHz\n',
          '+2.999825333s 1 WifiPhy:GetTxPowerForTransmission(): [INFO ] txPowerDbm=17 after applying m_powerDensityLimit=100\n'
          'WifiPhy:AddStaticPhyEntity(HR/DSSS) \n',
          '+0.000000000s -1 WifiPhy:SetChannelNumber): [DEBUG] Saving channel number configuration for initialization \n',
          '+0.000000000s -1 WifiPhy:SetChannelNumber(): DEBUG] Saving channel number configuration for initialization \n',
          '+0.000000000s WifiPhy:SetChannelNumber(): [DEBUG] Saving channel number configuration for initialization \n',
          '+0.000000000s -1 WifiPhy:SetChannelNumber(): Saving channel number configuration for initialization \n',
          '+0.000000000s -1 WifiPhy:SetChannelNumber():  \n',
          ]

expected_list = [{
                    'index': 0,
                    'time': 0.000000000,
                    'context': '-1',
                    'extended_context': 'node -1',
                    'component': 'FrameExchangeManager',
                    'function': 'SetWifiMac',
                    'arguments': '0x5576595683e0, 0x557659603820',
                    'severity_class': 'FUNCTION',
                    'message': ''
                },
                {
                    'index': 1,
                    'time': 0.045510017,
                    'context': '1',
                    'extended_context': 'mac=00:00:00:00:00:01',
                    'component': 'FrameExchangeManager',
                    'function': 'RxStartIndication',
                    'arguments': '0x5576595683e0, "PSDU reception started for ", +76us, " (txVector: ", txpwrlvl: 17 preamble: LONG channel width: 20 GI: 800 NTx: 97 Ness: 0 MPDU aggregation: 0 STBC: 0 FEC coding: BCC mode: OfdmRate6Mbps Nss: 1, ")"',
                    'severity_class': 'FUNCTION',
                    'message': ''
                },
                {
                    'index': 2,
                    'time': 0.000000000,
                    'context': '-1',
                    'extended_context': None,
                    'component': 'WifiPhy',
                    'function': 'SetChannelNumber',
                    'arguments': '',
                    'severity_class': 'DEBUG',
                    'message': 'Saving channel number configuration for initialization'
                },
                {
                    'index': 3,
                    'time': 0.506390387,
                    'context': '1',
                    'extended_context': 'mac=00:00:00:00:00:01',
                    'component': 'FrameExchangeManager',
                    'function': 'StartTransmission',
                    'arguments': '',
                    'severity_class': 'DEBUG',
                    'message': 'MPDU payload size=36, to=00:00:00:00:00:02, seq=16'
                },
                {
                    'index': 4,
                     'time': 2.999074264,
                     'context': '0',
                     'extended_context': 'mac=00:00:00:00:00:02',
                     'component': 'FrameExchangeManager',
                     'function': 'NotifyReceivedNormalAck',
                     'arguments': '0x56239764d8c0, DATA, payloadSize=1456, to=00:00:00:00:00:01, seqN=2323, duration/ID=+44000ns, lifetime=+195539us, packet=0x56239786dd00',
                     'severity_class': 'FUNCTION',
                     'message': ''
                 },
                {
                    'index': 5,
                    'time': 0.000000000,
                    'context': '-1',
                    'extended_context': None,
                    'component': 'WifiPhy',
                    'function': 'WifiPhy',
                    'arguments': '0x557659571bd0',
                    'severity_class': 'FUNCTION',
                    'message': ''
                },
                {
                    'index': 6,
                    'time': 0.000000000,
                    'context': '-1',
                    'extended_context': None,
                    'component': 'WifiPhy',
                    'function': 'SetChannelNumber',
                    'arguments': '',
                    'severity_class': 'INFO',
                    'message': ':()[]:./-='
                },
                {
                    'index': 7,
                     'time': 2.999825333,
                     'context': '1',
                     'extended_context': None,
                     'component': 'WifiPhy',
                     'function': 'GetTxPowerForTransmission',
                     'arguments': '',
                     'severity_class': 'DEBUG',
                     'message': 'txPowerDbm=17 with txPowerDbmPerMhz=3.9897 over 20 MHz'
                 },
                {
                    'index': 8,
                     'time': 2.999825333,
                     'context': '1',
                     'extended_context': None,
                     'component': 'WifiPhy',
                     'function': 'GetTxPowerForTransmission',
                     'arguments': '',
                     'severity_class': 'INFO',
                     'message': 'txPowerDbm=17 after applying m_powerDensityLimit=100'
                 }]


def test_parse_logs():
    data_dir = os.path.join(os.curdir, 'tests', str(time.strftime("%Y-%m-%d::%H-%M-%S")) + ':test_logs.json')
    try:
        with open(data_dir, "w") as f:
            f.writelines(log_ls)

        with pytest.warns(RuntimeWarning):
            parse_list = parse_logs(data_dir)
        assert len(parse_list) == len(expected_list)
        assert all([actual == expected for actual, expected in zip(parse_list, expected_list)])
    finally:
        os.remove(data_dir)


def test_filters():
    db_dir = os.path.join(os.curdir, 'tests', str(time.strftime("%Y-%m-%d::%H-%M-%S")) + ':test_logs.json')
    data_dir = os.path.join(os.curdir, 'tests', str(time.strftime("%Y-%m-%d::%H-%M-%S")) + ':test_logs')

    try:
        db = TinyDB(db_dir,
                    storage=CachingMiddleware(JSONStorage))

        with open(data_dir, "w") as f:
            f.writelines(log_ls)

        with pytest.warns(RuntimeWarning):
            parse_list = parse_logs(data_dir)
        insert_logs(parse_list, db)

        # Test case 1
        filter_list = filter_logs(db, context=['1'])
        expected_filter_list = [exp_list for exp_list in expected_list
                                if exp_list['context'] == '1']
        assert len(filter_list) == len(expected_filter_list)
        assert all([actual == expected for actual, expected
                    in zip(filter_list, expected_filter_list)])

        # Test case 2
        filter_list = filter_logs(db, context=['1'],
                                  function='GetTxPowerForTransmission')
        expected_filter_list = [exp_list for exp_list in expected_list
                                if (exp_list['context'] == '1' and
                                    exp_list['function'] == 'GetTxPowerForTransmission')]
        assert len(filter_list) == len(expected_filter_list)
        assert all([actual == expected for actual, expected
                    in zip(filter_list, expected_filter_list)])

        # Test case 3
        filter_list = filter_logs(db, context=['1'], severity_class='info')
        expected_filter_list = [exp_list for exp_list in expected_list
                                if (exp_list['context'] == '1' and
                                    exp_list['severity_class'] == 'INFO')]
        assert len(filter_list) == len(expected_filter_list)
        assert all([actual == expected for actual, expected
                    in zip(filter_list, expected_filter_list)])

        # Test case 4
        filter_list = filter_logs(db, context=[1], time_begin=0.6)
        expected_filter_list = [exp_list for exp_list in expected_list
                                if (exp_list['context'] == '1' and
                                    exp_list['time'] >= 0.6)]
        assert len(filter_list) == len(expected_filter_list)
        assert all([actual == expected for actual, expected
                    in zip(filter_list, expected_filter_list)])

        # Test case 5
        filter_list = filter_logs(db, context='1', time_end='0.5')
        expected_filter_list = [exp_list for exp_list in expected_list
                                if (exp_list['context'] == '1' and
                                    exp_list['time'] < 0.5)]
        assert len(filter_list) == len(expected_filter_list)
        assert all([actual == expected for actual, expected
                    in zip(filter_list, expected_filter_list)])

        # Test case 6
        filter_list = filter_logs(db, severity_class='function')
        expected_filter_list = [exp_list for exp_list in expected_list
                                if (exp_list['severity_class'] == 'FUNCTION')]
        assert len(filter_list) == len(expected_filter_list)
        assert all([actual == expected for actual, expected
                    in zip(filter_list, expected_filter_list)])

        # Test case 7
        filter_list = filter_logs(db, components={'WifiPhy': 'warn'})
        expected_filter_list = [exp_list for exp_list in expected_list
                                if (exp_list['component'] == 'WifiPhy' and
                                    exp_list['severity_class'] == 'WARN')]
        assert len(filter_list) == len(expected_filter_list)
        assert all([actual == expected for actual, expected
                    in zip(filter_list, expected_filter_list)])

        # Test case 8
        filter_list = filter_logs(db, components={'WifiPhy': 'info'})
        expected_filter_list = [exp_list for exp_list in expected_list
                                if (exp_list['component'] == 'WifiPhy' and
                                    exp_list['severity_class'] == 'INFO')]
        assert len(filter_list) == len(expected_filter_list)
        assert all([actual == expected for actual, expected
                    in zip(filter_list, expected_filter_list)])

        # Test case 9
        filter_list = filter_logs(db, components={'WifiPhy': ['info', 'debug']})
        expected_filter_list = [exp_list for exp_list in expected_list
                                if (exp_list['component'] == 'WifiPhy') and
                                   (exp_list['severity_class'] == 'INFO' or
                                    exp_list['severity_class'] == 'DEBUG')]
        assert len(filter_list) == len(expected_filter_list)
        assert all([actual == expected for actual, expected
                    in zip(filter_list, expected_filter_list)])

        # Test case 10
        filter_list = filter_logs(db,
                                  components={'WifiPhy': ['info', 'debug']},
                                  severity_class='function')
        expected_filter_list = [exp_list for exp_list in expected_list
                                if (exp_list['severity_class'] == 'FUNCTION') or
                                   ((exp_list['component'] == 'WifiPhy') and
                                    (exp_list['severity_class'] == 'INFO' or
                                     exp_list['severity_class'] == 'DEBUG'))]
        assert len(filter_list) == len(expected_filter_list)
        assert all([actual == expected for actual, expected
                    in zip(filter_list, expected_filter_list)])

        # Test case 11
        with pytest.raises(TypeError):
            filter_list = filter_logs(db, context=1.0, time_end=0.5)

        # Test case 12
        with pytest.raises(TypeError):
            filter_list = filter_logs(db, time_end=[0.5])

        # Test case 13
        with pytest.raises(TypeError):
            filter_list = filter_logs(db, time_end=['0.5'])
    finally:
        wipe_results(db, db_dir)
        os.remove(data_dir)
