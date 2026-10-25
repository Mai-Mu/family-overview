import io
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import zipfile

from server import Store, AppError, amount_sum, bounds, summarize, make_server


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def save(self, module, **data):
        return self.store.save(module, {'data': data})

    def test_all_blank_and_zero_are_distinct_and_persistent(self):
        blank = self.save('assets')
        zero = self.save('assets', value={'value': '0'}, currency='CNY')
        self.assertIsNone(blank['data']['value'])
        self.assertEqual(zero['data']['value']['value'], '0')
        reopened = Store(self.tmp.name)
        summary = summarize(reopened.state())
        self.assertEqual(summary['currencies']['CNY']['assets']['lower'], '0')
        self.assertEqual(summary['pending_count'], 1)

    def test_every_module_can_save_empty(self):
        for name in ('members','assets','liabilities','receivables','guarantees','recurring_rules','commitments','protection'):
            record = self.save(name)
            self.assertTrue(all(value is None for value in record['data'].values()))

    def test_multiple_currencies_and_open_ranges(self):
        self.save('assets', value={'lower': '100', 'upper': None}, currency='CNY')
        self.save('assets', value={'value': '20'}, currency='USD')
        result = summarize(self.store.state())['currencies']
        self.assertEqual(result['CNY']['assets']['lower'], '100')
        self.assertIsNone(result['CNY']['assets']['upper'])
        self.assertEqual(result['USD']['assets']['lower'], '20')

    def test_decimal_sum_does_not_use_float_arithmetic(self):
        self.assertEqual(amount_sum([bounds('0.1'), bounds('0.2')])['lower'], '0.3')

    def test_reversed_range_is_not_a_valid_total(self):
        self.save('assets',value={'lower':'200','upper':'100'},currency='CNY')
        result=summarize(self.store.state())
        self.assertEqual(result['currencies'],{})
        self.assertEqual(result['pending_count'],1)

    def test_person_pending_count_excludes_other_members(self):
        a=self.save('members',display_name='测试成员甲')
        b=self.save('members',display_name='测试成员乙')
        self.save('recurring_rules',payer_ids=[b['id']])
        self.assertEqual(summarize(self.store.state(),a['id'])['pending_count'],0)

    def test_member_views_do_not_split_shared_assets(self):
        a = self.save('members', display_name='测试成员甲')
        b = self.save('members', display_name='测试成员乙')
        self.save('assets', owner_ids=[a['id'],b['id']], value={'value':'100'}, currency='CNY')
        result = summarize(self.store.state(), a['id'])
        self.assertEqual(result['currencies'], {})
        self.assertEqual(result['shared_count'], 1)

    def test_shared_rule_uses_explicit_allocation(self):
        a = self.save('members', display_name='测试成员甲')
        b = self.save('members', display_name='测试成员乙')
        self.save('recurring_rules', direction='支出', status='生效', frequency='每月', currency='CNY',
                  expected_amount={'value':'100'}, payer_ids=[a['id'],b['id']],
                  payer_allocations=[{'member_id':a['id'],'percentage':'30'}])
        result = summarize(self.store.state(),a['id'])
        self.assertEqual(result['currencies']['CNY']['expense']['lower'],'30')

    def test_internal_transfers_and_paused_rules_are_excluded(self):
        self.save('recurring_rules', direction='家庭内部支持或转账', status='生效', frequency='每月', currency='CNY', expected_amount={'value':'100'})
        self.save('recurring_rules', direction='支出', status='暂停', frequency='每月', currency='CNY', expected_amount={'value':'100'})
        self.assertEqual(summarize(self.store.state())['currencies'],{})

    def test_forecast_is_not_actual_paid_or_a_loan_balance_update(self):
        loan=self.save('liabilities', remaining_principal='1000',currency='CNY')
        self.save('recurring_rules',direction='支出',status='生效',frequency='每月',currency='CNY',
                  expected_amount={'value':'100'},linked_liability_id=loan['id'])
        state=self.store.state()
        self.assertEqual(summarize(state)['currencies']['CNY']['expense']['lower'],'100')
        self.assertEqual(self.store.get(loan['id'])['data']['remaining_principal'],'1000')
        self.assertEqual(len([r for r in state if r['module']=='commitments']),0)

    def test_loan_and_rule_are_not_added_twice_to_expense(self):
        loan=self.save('liabilities',remaining_principal='1000',regular_payment={'value':'100'},currency='CNY')
        self.save('recurring_rules',direction='支出',status='生效',frequency='每月',currency='CNY',
                  expected_amount={'value':'100'},linked_liability_id=loan['id'])
        self.assertEqual(summarize(self.store.state())['currencies']['CNY']['expense']['lower'],'100')

    def test_linked_loan_progress_saved_atomically(self):
        saved=self.store.save('liabilities',{'data':{'liability_name':'测试贷款','currency':'CNY'},
                   'linked_commitment':{'data':{'confirmed_paid_amount':'200','paid_as_of':'2026-10'}}})
        child=self.store.get(saved['data']['linked_commitment_id'])
        self.assertEqual(child['data']['confirmed_paid_amount'],'200')
        self.assertEqual(child['data']['linked_liability_id'],saved['id'])
        self.assertEqual(child['data']['currency'],'CNY')
        self.assertEqual(len(self.store.state()),2)

    def test_version_conflict_does_not_overwrite(self):
        first=self.save('assets',asset_name='测试原名')
        self.store.save('assets',{'data':{'asset_name':'测试新名'},'version':first['version']},first['id'])
        with self.assertRaises(AppError) as error:
            self.store.save('assets',{'data':{'asset_name':'冲突名称'},'version':first['version']},first['id'])
        self.assertEqual(error.exception.status,409)
        self.assertEqual(self.store.get(first['id'])['data']['asset_name'],'测试新名')
        self.assertEqual(len(self.store.history(first['id'])),2)

    def test_soft_delete_and_restore(self):
        record=self.save('assets',value={'value':'50'},currency='CNY')
        self.store.remove(record['id'])
        self.assertEqual(summarize(self.store.state())['currencies'],{})
        self.store.remove(record['id'],restore=True)
        self.assertEqual(summarize(self.store.state())['currencies']['CNY']['assets']['lower'],'50')

    def test_attachment_unicode_and_backup_database(self):
        record=self.save('assets')
        self.store.add_attachment(record['id'],'测试材料.txt','测试内容'.encode(),'text/plain')
        saved=self.store.get(record['id'])
        info,content=self.store.attachment(saved['attachments'][0]['id'])
        self.assertEqual(info['filename'],'测试材料.txt')
        self.assertEqual(content,'测试内容'.encode())
        with zipfile.ZipFile(io.BytesIO(self.store.backup())) as archive:
            self.assertIn('family.sqlite3',archive.namelist())
            self.assertIn('records.json',archive.namelist())
            self.assertTrue(any(n.startswith('uploads/') for n in archive.namelist()))
            path=Path(self.tmp.name)/'restored.sqlite3'
            path.write_bytes(archive.read('family.sqlite3'))
        with closing(sqlite3.connect(path)) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM records').fetchone()[0],1)

    def test_invalid_reference_rolled_back(self):
        with self.assertRaises(AppError):
            self.save('assets',owner_ids=['missing'])
        self.assertEqual(self.store.state(),[])

    def test_setup_members_is_idempotent(self):
        self.store.setup_members()
        self.store.setup_members()
        self.assertEqual(len(self.store.state()),3)


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.server=make_server(self.tmp.name,0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.base=f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.tmp.cleanup()

    def test_http_save_reload_and_foreign_origin(self):
        request=Request(self.base+'/api/records/commitments',data=b'{"data":{}}',headers={'Content-Type':'application/json'},method='POST')
        with urlopen(request) as response:
            saved=json.load(response)
        with urlopen(self.base+'/api/state') as response:
            self.assertEqual(json.load(response)['records'][0]['id'],saved['id'])
        request=Request(self.base+'/api/records/commitments',data=b'{}',headers={'Origin':'http://unrelated.invalid'},method='POST')
        with self.assertRaises(HTTPError) as error:
            urlopen(request)
        self.assertEqual(error.exception.code,403)

    def test_static_files_do_not_expose_database_or_sources(self):
        for path in ('/data/family.sqlite3','/server.py','/../server.py'):
            with self.assertRaises(HTTPError) as error:
                urlopen(self.base+path)
            self.assertEqual(error.exception.code,404)
        with urlopen(self.base+'/') as response:
            self.assertEqual(response.status,200)


if __name__=='__main__':
    unittest.main()
