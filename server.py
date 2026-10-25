"""Local family finance app. Standard library only; business data stays on device."""
from __future__ import annotations
import argparse
from contextlib import contextmanager, closing
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
import mimetypes
from pathlib import Path
import re
import sqlite3
import tempfile
import threading
import uuid
from urllib.parse import unquote, urlparse, quote, parse_qs
import webbrowser
import zipfile

ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / 'design' / '家庭经济信息收集字段定义.json'
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))
MODULES = {m['key']: m for m in SCHEMA['modules']}
HK = timezone(timedelta(hours=8))
LOCK = threading.RLock()


def now():
    return datetime.now(HK).isoformat(timespec='milliseconds')


def uid():
    return uuid.uuid4().hex


def dumps(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def decimal(value):
    try:
        if value is None or isinstance(value, bool) or str(value).strip() == '':
            return None
        d = Decimal(str(value).replace(',', '').strip())
        return d if d.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


def bounds(value):
    if isinstance(value, dict):
        exact = decimal(value.get('value'))
        if exact is not None:
            return exact, exact
        lo, hi = decimal(value.get('lower')), decimal(value.get('upper'))
        return (None, None) if lo is not None and hi is not None and lo > hi else (lo, hi)
    d = decimal(value)
    return d, d


def amount_sum(values):
    values = [v for v in values if v != (None, None)]
    if not values:
        return None
    lo = sum((v[0] for v in values), Decimal(0)) if all(v[0] is not None for v in values) else None
    hi = sum((v[1] for v in values), Decimal(0)) if all(v[1] is not None for v in values) else None
    return {'lower': str(lo) if lo is not None else None,
            'upper': str(hi) if hi is not None else None, 'count': len(values)}


class AppError(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status


class Store:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.uploads = self.directory / 'uploads'
        self.uploads.mkdir(exist_ok=True)
        self.db = self.directory / 'family.sqlite3'
        with self.connect() as c:
            c.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS records (
                  id TEXT PRIMARY KEY,module TEXT NOT NULL,data_json TEXT NOT NULL,
                  version INTEGER NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,deleted_at TEXT);
                CREATE INDEX IF NOT EXISTS records_module ON records(module,deleted_at);
                CREATE TABLE IF NOT EXISTS history (
                  id INTEGER PRIMARY KEY,record_id TEXT NOT NULL,module TEXT NOT NULL,
                  version INTEGER NOT NULL,event TEXT NOT NULL,data_json TEXT NOT NULL,created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS record_links (
                  record_id TEXT NOT NULL,field_key TEXT NOT NULL,target_id TEXT NOT NULL,
                  PRIMARY KEY(record_id,field_key,target_id));
                CREATE TABLE IF NOT EXISTS allocations (
                  record_id TEXT NOT NULL,field_key TEXT NOT NULL,position INTEGER NOT NULL,
                  member_id TEXT,amount TEXT,percentage TEXT,note TEXT,
                  PRIMARY KEY(record_id,field_key,position));
                CREATE TABLE IF NOT EXISTS attachments (
                  id TEXT PRIMARY KEY,record_id TEXT NOT NULL,filename TEXT NOT NULL,
                  storage_name TEXT NOT NULL,mime TEXT NOT NULL,size INTEGER NOT NULL,created_at TEXT NOT NULL);
            ''')

    @contextmanager
    def connect(self):
        c = sqlite3.connect(self.db, timeout=15)
        c.row_factory = sqlite3.Row
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()

    def fields(self, module):
        if module not in MODULES:
            raise AppError('没有这个信息模块', 404)
        return MODULES[module]['fields'] + SCHEMA['shared_fields']

    def normalize(self, module, raw):
        if not isinstance(raw, dict):
            raise AppError('记录格式不正确')
        result = {}
        for f in self.fields(module):
            v = raw.get(f['key'])
            if v == '' or v == [] or v == {}:
                v = None
            if isinstance(v, str):
                v = v.strip() or None
            if f['type'] == 'attachment_list':
                v = None
            elif f['type'] == 'money_or_range' and v is not None:
                if not isinstance(v, dict):
                    v = {'value': str(v), 'lower': None, 'upper': None}
                v = {k: (str(v[k]).strip() or None) if v.get(k) is not None else None for k in ('value', 'lower', 'upper')}
                if not any(x is not None for x in v.values()):
                    v = None
            elif f['type'] in ('money', 'percentage', 'decimal', 'integer', 'year') and v is not None:
                v = str(v)
            elif f['type'] == 'allocation_rows' and v is not None:
                if not isinstance(v, list):
                    raise AppError('分担明细格式不正确')
                v = [{k: (str(row.get(k)).strip() or None) if row.get(k) is not None else None
                      for k in ('member_id', 'amount', 'percentage', 'agreement_note')}
                     for row in v if isinstance(row, dict)] or None
            elif f['type'] == 'references' and v is not None:
                if not isinstance(v, list) or any(not isinstance(x, str) for x in v):
                    raise AppError('关联选择格式不正确')
                v = list(dict.fromkeys(v)) or None
            elif f['type'] in ('reference', 'text', 'long_text', 'choice', 'currency', 'partial_date') and v is not None:
                if not isinstance(v, str):
                    raise AppError('字段格式不正确：' + f['label'])
            result[f['key']] = v
        if len(dumps(result)) > 500000:
            raise AppError('这条记录内容过长')
        return result

    def validate_refs(self, c, module, data):
        for f in self.fields(module):
            value = data.get(f['key'])
            if f.get('references') and value is not None:
                ids = value if f['type'] == 'references' else [value]
                for target in ids:
                    row = c.execute('SELECT module FROM records WHERE id=?', (target,)).fetchone()
                    if row is None or row['module'] != f['references']:
                        raise AppError('关联记录不存在，请重新选择：' + f['label'])
            if f['type'] == 'allocation_rows' and value:
                for share in value:
                    if share.get('member_id'):
                        row = c.execute("SELECT id FROM records WHERE id=? AND module='members'", (share['member_id'],)).fetchone()
                        if row is None:
                            raise AppError('分担成员不存在，请重新选择')

    def reindex(self, c, module, record_id, data):
        c.execute('DELETE FROM record_links WHERE record_id=?', (record_id,))
        c.execute('DELETE FROM allocations WHERE record_id=?', (record_id,))
        for f in self.fields(module):
            v = data.get(f['key'])
            if f.get('references') and v:
                for target in (v if f['type'] == 'references' else [v]):
                    c.execute('INSERT OR IGNORE INTO record_links VALUES(?,?,?)', (record_id, f['key'], target))
            if f['type'] == 'allocation_rows' and v:
                for i, share in enumerate(v):
                    c.execute('INSERT INTO allocations VALUES(?,?,?,?,?,?,?)',
                              (record_id, f['key'], i, share.get('member_id'), share.get('amount'),
                               share.get('percentage'), share.get('agreement_note')))

    def serialize(self, c, row):
        if row is None:
            raise AppError('记录不存在', 404)
        d = dict(row)
        d['data'] = json.loads(d.pop('data_json'))
        d['attachments'] = [dict(a) for a in c.execute(
            'SELECT id,filename,mime,size,created_at FROM attachments WHERE record_id=? ORDER BY created_at', (d['id'],))]
        return d

    def state(self):
        with self.connect() as c:
            rows = c.execute('SELECT * FROM records ORDER BY updated_at DESC').fetchall()
            return [self.serialize(c, row) for row in rows]

    def get(self, record_id):
        with self.connect() as c:
            return self.serialize(c, c.execute('SELECT * FROM records WHERE id=?', (record_id,)).fetchone())

    def _write(self, c, module, record_id, raw, expected_version=None):
        data = self.normalize(module, raw)
        self.validate_refs(c, module, data)
        previous = c.execute('SELECT * FROM records WHERE id=?', (record_id,)).fetchone()
        stamp = now()
        if previous:
            if previous['module'] != module:
                raise AppError('模块不匹配')
            if expected_version is not None and previous['version'] != expected_version:
                raise AppError('这条记录已在其他窗口修改。请保留当前内容，刷新后核对再保存。', 409)
            version = previous['version'] + 1
            c.execute('UPDATE records SET data_json=?,version=?,updated_at=? WHERE id=?', (dumps(data), version, stamp, record_id))
        else:
            version = 1
            c.execute('INSERT INTO records VALUES(?,?,?,?,?,?,NULL)', (record_id, module, dumps(data), version, stamp, stamp))
        self.reindex(c, module, record_id, data)
        c.execute('INSERT INTO history(record_id,module,version,event,data_json,created_at) VALUES(?,?,?,?,?,?)',
                  (record_id, module, version, '修改' if previous else '创建', dumps(data), stamp))
        return record_id

    def save(self, module, payload, record_id=None):
        self.fields(module)
        record_id = record_id or uid()
        with LOCK, self.connect() as c:
            data = dict(payload.get('data') or {})
            linked = payload.get('linked_commitment')
            if module == 'liabilities' and isinstance(linked, dict):
                child = linked.get('data') or {}
                existing_id = data.get('linked_commitment_id')
                if existing_id or any(v not in (None, '', [], {}) for v in child.values()):
                    child_id = existing_id or uid()
                    # Insert a new parent before validating the child's back-reference.
                    if c.execute('SELECT id FROM records WHERE id=?', (record_id,)).fetchone() is None:
                        self._write(c, module, record_id, {k: v for k, v in data.items() if k != 'linked_commitment_id'})
                    child = dict(child)
                    child['linked_liability_id'] = record_id
                    if not existing_id:
                        if data.get('liability_name') and not child.get('title'):
                            child['title'] = data['liability_name'] + '还款约定'
                        if child.get('currency') is None:
                            child['currency'] = data.get('currency')
                        if child.get('payer_ids') is None:
                            child['payer_ids'] = data.get('payer_ids')
                        if child.get('spending_pattern') is None:
                            child['spending_pattern'] = '贷款还款'
                    self._write(c, 'commitments', child_id, child, linked.get('version'))
                    data['linked_commitment_id'] = child_id
            self._write(c, module, record_id, data, payload.get('version'))
        return self.get(record_id)

    def remove(self, record_id, restore=False):
        with LOCK, self.connect() as c:
            row = c.execute('SELECT * FROM records WHERE id=?', (record_id,)).fetchone()
            if row is None:
                raise AppError('记录不存在', 404)
            stamp, version = now(), row['version'] + 1
            c.execute('UPDATE records SET deleted_at=?,updated_at=?,version=? WHERE id=?',
                      (None if restore else stamp, stamp, version, record_id))
            c.execute('INSERT INTO history(record_id,module,version,event,data_json,created_at) VALUES(?,?,?,?,?,?)',
                      (record_id, row['module'], version, '恢复' if restore else '移除', row['data_json'], stamp))
        return self.get(record_id)

    def history(self, record_id):
        with self.connect() as c:
            return [dict(r, data=json.loads(r['data_json'])) for r in c.execute(
                'SELECT * FROM history WHERE record_id=? ORDER BY id DESC', (record_id,))]

    def setup_members(self):
        with LOCK, self.connect() as c:
            roles = {json.loads(r[0]).get('family_role') for r in c.execute("SELECT data_json FROM records WHERE module='members' AND deleted_at IS NULL")}
            for name, role in [('我', '本人'), ('父亲', '父亲'), ('母亲', '母亲')]:
                if role not in roles:
                    self._write(c, 'members', uid(), {'display_name': name, 'family_role': role})
        return self.state()

    def add_attachment(self, record_id, filename, content, mime):
        self.get(record_id)
        if len(content) > 25 * 1024 * 1024:
            raise AppError('单个附件请控制在25MB以内')
        filename = Path(filename.replace('\\', '/')).name.replace('\r', '').replace('\n', '')[:240] or '未命名资料'
        attachment_id = uid()
        suffix = Path(filename).suffix[:12]
        storage_name = attachment_id + suffix
        with LOCK:
            destination = self.uploads / storage_name
            destination.write_bytes(content)
            try:
                with self.connect() as c:
                    c.execute('INSERT INTO attachments VALUES(?,?,?,?,?,?,?)',
                              (attachment_id, record_id, filename, storage_name, mime or 'application/octet-stream', len(content), now()))
            except Exception:
                destination.unlink(missing_ok=True)
                raise
        return self.get(record_id)

    def attachment(self, attachment_id):
        with self.connect() as c:
            row = c.execute('SELECT * FROM attachments WHERE id=?', (attachment_id,)).fetchone()
            if row is None:
                raise AppError('附件不存在', 404)
            return dict(row), (self.uploads / row['storage_name']).read_bytes()

    def backup(self):
        output = BytesIO()
        with LOCK, tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'family.sqlite3'
            with self.connect() as source, closing(sqlite3.connect(path)) as destination:
                source.backup(destination)
            with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.write(path, 'family.sqlite3')
                archive.writestr('records.json', dumps({'exported_at': now(), 'records': self.state()}))
                archive.writestr('field-schema.json', dumps(SCHEMA))
                with self.connect() as c:
                    for row in c.execute('SELECT storage_name FROM attachments'):
                        file = self.uploads / row['storage_name']
                        if file.is_file():
                            archive.write(file, 'uploads/' + row['storage_name'])
        return output.getvalue()


def scoped_amount(data, key, members_key, member_id, shares_key=None):
    value = bounds(data.get(key))
    if not member_id:
        return value, False
    members = data.get(members_key) or []
    if member_id not in members:
        return (None, None), False
    if len(members) == 1:
        return value, False
    for share in data.get(shares_key, []) or []:
        if share.get('member_id') != member_id:
            continue
        amount, percentage = decimal(share.get('amount')), decimal(share.get('percentage'))
        if amount is not None:
            return (amount, amount), False
        if percentage is not None:
            return tuple(v * percentage / 100 if v is not None else None for v in value), False
    return (None, None), True


def summarize(records, member_id=None):
    active = [r for r in records if not r['deleted_at']]
    grouped = {}
    pending, shared = set(), set()
    factors = {'每周': Decimal(52) / 12, '每月': Decimal(1), '每季': Decimal(1) / 3,
               '每半年': Decimal(1) / 6, '每年': Decimal(1) / 12}
    today = datetime.now(HK).date().isoformat()
    for r in active:
        d, module = r['data'], r['module']
        if member_id:
            fields = [f for f in MODULES[module]['fields'] if f.get('references') == 'members']
            associated = [v for f in fields for v in
                          ((d.get(f['key']) or []) if f['type'] == 'references' else [d.get(f['key'])])]
            if member_id not in associated:
                continue
        currency = (d.get('currency') or '').upper()
        metric, key, people, shares = None, None, None, None
        if module == 'assets':
            metric, key, people = 'assets', 'value', 'owner_ids'
        elif module == 'liabilities':
            if d.get('counterparty_scope') == '家庭内部':
                continue
            metric, key, people = 'liabilities', 'remaining_principal', 'borrower_ids'
        elif module == 'recurring_rules':
            if d.get('direction') == '家庭内部支持或转账' or d.get('status') in ('暂停', '终止'):
                continue
            metric = {'收入': 'income', '支出': 'expense'}.get(d.get('direction'))
            key = 'expected_amount'
            people = 'income_owner_ids' if metric == 'income' else 'payer_ids'
            shares = 'payer_allocations' if metric == 'expense' else None
            if d.get('status') != '生效' or d.get('frequency') not in factors or not metric:
                pending.add(r['id'])
                continue
            start, end = d.get('effective_from'), d.get('effective_until')
            if start and re.fullmatch(r'\d{4}(-\d{2})?(-\d{2})?', start) and today[:len(start)] < start:
                continue
            if end and re.fullmatch(r'\d{4}(-\d{2})?(-\d{2})?', end) and today[:len(end)] > end:
                continue
        if not metric:
            continue
        value, joint = scoped_amount(d, key, people, member_id, shares)
        if joint:
            shared.add(r['id'])
            continue
        if member_id and member_id not in (d.get(people) or []):
            continue
        if value == (None, None) or not currency:
            pending.add(r['id'])
            continue
        if module == 'recurring_rules':
            value = tuple(v * factors[d['frequency']] if v is not None else None for v in value)
        grouped.setdefault(currency, {'assets': [], 'liabilities': [], 'income': [], 'expense': []})[metric].append(value)
    result = {currency: {k: amount_sum(v) for k, v in items.items()} for currency, items in grouped.items()}
    return {'currencies': result, 'pending_count': len(pending), 'shared_count': len(shared),
            'record_count': len(active), 'as_of': today}


class Handler(BaseHTTPRequestHandler):
    server_version = 'FamilyLocal/1.0'

    def log_message(self, fmt, *args):
        # Request paths only; no payloads or financial values in logs.
        if self.path == '/api/health':
            return
        super().log_message(fmt, *args)

    def send(self, status, content, content_type='application/json; charset=utf-8', extra=None):
        if not isinstance(content, bytes):
            content = dumps(content).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(content)

    def body(self):
        size = int(self.headers.get('Content-Length') or 0)
        if size > 32 * 1024 * 1024:
            raise AppError('上传内容过大', 413)
        return self.rfile.read(size)

    def check_origin(self):
        allowed = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        if self.headers.get('Host') not in allowed:
            raise AppError('仅支持本机访问', 403)
        origin = self.headers.get('Origin')
        if origin and origin not in {'http://' + host for host in allowed}:
            raise AppError('请求来源不匹配', 403)

    def do_GET(self):
        self.dispatch('GET')

    def do_POST(self):
        self.dispatch('POST')

    def do_PUT(self):
        self.dispatch('PUT')

    def do_DELETE(self):
        self.dispatch('DELETE')

    def dispatch(self, method):
        try:
            self.check_origin()
            path = unquote(urlparse(self.path).path)
            store = self.server.store
            if method == 'GET' and path == '/api/health':
                return self.send(200, {'ok': True, 'app': 'family-overview'})
            if method == 'GET' and path == '/api/schema':
                return self.send(200, SCHEMA)
            if method == 'GET' and path == '/api/state':
                records = store.state()
                return self.send(200, {'records': records, 'summary': summarize(records)})
            if method == 'GET' and path == '/api/summary':
                member = parse_qs(urlparse(self.path).query).get('member_id', [None])[0]
                return self.send(200, summarize(store.state(), member))
            if method == 'POST' and path == '/api/setup-members':
                return self.send(200, {'records': store.setup_members()})
            if method == 'GET' and path == '/api/backup':
                return self.send(200, store.backup(), 'application/zip', {'Content-Disposition': 'attachment; filename="family-backup-' + datetime.now(HK).strftime('%Y%m%d-%H%M%S') + '.zip"'})
            match = re.fullmatch(r'/api/records/([a-z_]+)(?:/([a-f0-9]+))?(?:/(history|restore|attachments))?', path)
            if match:
                module, record_id, action = match.groups()
                store.fields(module)
                if record_id and store.get(record_id)['module'] != module:
                    raise AppError('模块不匹配', 404)
                if action == 'history' and method == 'GET':
                    return self.send(200, {'history': store.history(record_id)})
                if action == 'restore' and method == 'POST':
                    return self.send(200, store.remove(record_id, restore=True))
                if action == 'attachments' and method == 'POST':
                    body = self.body()
                    content_type = self.headers.get('Content-Type', '')
                    if not content_type.startswith('multipart/form-data;'):
                        raise AppError('请选择要上传的文件')
                    message = BytesParser(policy=policy.default).parsebytes(
                        ('Content-Type: ' + content_type + '\r\nMIME-Version: 1.0\r\n\r\n').encode() + body)
                    for part in message.iter_parts():
                        if part.get_filename():
                            store.add_attachment(record_id, part.get_filename(), part.get_payload(decode=True) or b'', part.get_content_type())
                    return self.send(200, store.get(record_id))
                if not action and method in ('POST', 'PUT'):
                    payload = json.loads(self.body() or b'{}')
                    return self.send(200, store.save(module, payload, record_id))
                if not action and record_id and method == 'DELETE':
                    return self.send(200, store.remove(record_id))
                if not action and method == 'GET':
                    return self.send(200, store.get(record_id) if record_id else {'records': [r for r in store.state() if r['module'] == module]})
            match = re.fullmatch(r'/api/attachments/([a-f0-9]+)', path)
            if match and method == 'GET':
                item, content = store.attachment(match[1])
                return self.send(200, content, 'application/octet-stream',
                                 {'Content-Disposition': "attachment; filename=\"document\"; filename*=UTF-8''" + quote(item['filename'])})
            if method == 'GET' and not path.startswith('/api/'):
                if path.startswith('/design/'):
                    base, relative = ROOT / 'design', path.removeprefix('/design/')
                else:
                    base, relative = ROOT / 'web', path.lstrip('/') or 'index.html'
                destination = (base / relative).resolve()
                if destination.is_relative_to(base.resolve()) and destination.is_file():
                    mime = mimetypes.guess_type(destination.name)[0] or 'application/octet-stream'
                    if mime.startswith('text/') or mime in ('application/javascript', 'application/json'):
                        mime += '; charset=utf-8'
                    return self.send(200, destination.read_bytes(), mime)
            raise AppError('没有找到这个页面或接口', 404)
        except AppError as e:
            self.send(e.status, {'error': e.message})
        except (ValueError, TypeError, json.JSONDecodeError):
            self.send(400, {'error': '内容格式不正确，请检查后重试'})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            import traceback
            traceback.print_exc()
            self.send(500, {'error': '本地保存出现问题，请保留当前内容并重试'})


def make_server(directory=None, port=8765):
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.store = Store(directory or ROOT / 'data')
    server.daemon_threads = True
    return server


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--data-dir', default=str(ROOT / 'data'))
    parser.add_argument('--open', action='store_true')
    args = parser.parse_args()
    try:
        server = make_server(args.data_dir, args.port)
    except OSError:
        if args.open:
            try:
                from urllib.request import urlopen
                with urlopen(f'http://127.0.0.1:{args.port}/api/health', timeout=2) as response:
                    if json.load(response).get('app') == 'family-overview':
                        webbrowser.open(f'http://127.0.0.1:{args.port}')
                        raise SystemExit(0)
            except (OSError, ValueError):
                pass
        print('Port unavailable. Try: python server.py --port 8766', flush=True)
        raise SystemExit(1)
    url = f'http://127.0.0.1:{server.server_port}'
    print('Family overview is ready. Local: ' + url, flush=True)
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
