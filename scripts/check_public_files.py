"""Check tracked source files for runtime data and obvious private material.

This deliberately reports file names and line numbers, never matched values.
It is a small publication guard, not a complete secret-detection service.
"""
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BLOCKED_DIRS = {'data', 'uploads', 'backups', '.test-artifacts', '__pycache__', '.venv', 'venv', 'node_modules'}
BLOCKED_SUFFIXES = {'.db', '.sqlite', '.sqlite3', '.zip', '.bak', '.backup', '.pyc', '.pyo', '.pem', '.key', '.p12', '.pfx', '.log'}
PATTERNS = {
    'private-key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'access-token': re.compile(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}'),
    'machine-path': re.compile(r'[A-Za-z]:[\\/](?:Users|Works)[\\/]|/(?:Users|home)/[^\s/]+/'),
    'personal-email': re.compile(r'\b(?![^\s@]*@users\.noreply\.github\.com\b)[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
    'private-number': re.compile(r'(?<!\d)(?:1[3-9]\d{9}|\d{17}[\dXx])(?!\d)'),
}


def inspect_file(name, content):
    path = PurePosixPath(name)
    lower = path.name.lower()
    if (any(part in BLOCKED_DIRS for part in path.parts)
            or path.suffix.lower() in BLOCKED_SUFFIXES
            or re.search(r'\.(?:db|sqlite|sqlite3)-(?:wal|shm|journal)$', lower)
            or lower == '.env' or lower.startswith(('.env.', 'credentials', 'secrets'))):
        return [(name, None, 'excluded-file')]
    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError:
        if path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.svg', '.webp', '.ico'}:
            return []
        return [(name, None, 'unexpected-binary')]
    return [(name, number, label)
            for number, line in enumerate(text.splitlines(), 1)
            for label, pattern in PATTERNS.items() if pattern.search(line)]


def main():
    try:
        names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').split('\0')
    except (OSError, subprocess.CalledProcessError):
        print('Run this check from a Git checkout after adding source files.', file=sys.stderr)
        return 2
    findings = []
    for name in filter(None, names):
        content = subprocess.check_output(['git', 'show', ':' + name], cwd=ROOT)
        findings.extend(inspect_file(name, content))
    for name, line, label in findings:
        location = f'{name}:{line}' if line else name
        print(f'{location}: {label}')
    print(f'Checked {sum(bool(n) for n in names)} staged/tracked files; {len(findings)} finding(s).')
    return 1 if findings else 0


if __name__ == '__main__':
    raise SystemExit(main())
