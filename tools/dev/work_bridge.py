"""Cooperative single-writer sessions; local snapshots and verified Git push.

Python standard library only. Does not commit, merge, reset, or delete backups.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import zipfile


def git(repo, *args):
    return subprocess.check_output(
        ['git', '-C', str(repo), *args], stderr=subprocess.PIPE
    ).decode('utf-8', errors='surrogateescape').rstrip('\r\n')


def write_json(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)


def snapshot(repo, destination):
    destination.mkdir(parents=True, exist_ok=False)
    head = git(repo, 'rev-parse', 'HEAD')
    before = git(repo, 'status', '--porcelain=v1', '-uall')
    git(repo, 'bundle', 'create', str(destination / 'history.bundle'), '--all')
    git(repo, 'bundle', 'verify', str(destination / 'history.bundle'))
    names = git(repo, 'ls-files', '-z', '--cached', '--others', '--exclude-standard')
    hashes = {}
    deleted = []
    with zipfile.ZipFile(destination / 'working.zip', 'x', zipfile.ZIP_DEFLATED) as archive:
        total = 0
        for name in sorted(set(names.split('\0')) - {''}):
            path = repo / name
            if path.is_symlink() or not path.resolve().is_relative_to(repo):
                raise RuntimeError('Snapshot refuses symlinks or paths outside checkout')
            if not path.exists():
                deleted.append(name)
                continue
            if not path.is_file():
                raise RuntimeError('Submodules/directories require a separate backup')
            total += path.stat().st_size
            if total > 512 * 1024 * 1024:
                raise RuntimeError('Snapshot exceeds 512 MiB; arrange an asset backup')
            data = path.read_bytes()
            hashes[name] = hashlib.sha256(data).hexdigest()
            archive.writestr(name, data)
    with zipfile.ZipFile(destination / 'working.zip') as archive:
        for name, digest in hashes.items():
            if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise RuntimeError('Backup hash mismatch')
    # Detect source changes while copying; cooperative lock cannot stop editors.
    for name, digest in hashes.items():
        if hashlib.sha256((repo / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError('Source changed during backup; snapshot is incomplete')
    if head != git(repo, 'rev-parse', 'HEAD') or before != git(repo, 'status', '--porcelain=v1', '-uall'):
        raise RuntimeError('Checkout changed during backup')
    write_json(destination / 'manifest.json', {
        'head': head, 'sha256': hashes, 'deleted': deleted,
        'status': before, 'excluded': 'ignored files, unsaved editor buffers, external assets',
    })
    return str(destination)


def run(args):
    repo = Path(git(args.repo, 'rev-parse', '--show-toplevel')).resolve()
    common = Path(git(repo, 'rev-parse', '--path-format=absolute', '--git-common-dir'))
    lock = common / 'work-bridge-session.json'
    if args.action == 'status':
        print(lock.read_text() if lock.exists() else 'NO_ACTIVE_SESSION')
        print(git(repo, 'status', '--short', '--branch'))
        return
    if args.action == 'auto-checkpoint' and not lock.exists():
        print('IDLE: no active session')
        return
    # Short-lived exclusive guard prevents simultaneous bridge invocations.
    guard = common / 'work-bridge-operation.lock'
    fd = os.open(guard, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        if args.action == 'start':
            if lock.exists():
                raise RuntimeError('An active session exists; inspect status and coordinate')
            if not args.backup_root or not args.owner:
                raise RuntimeError('start requires --backup-root and --owner')
            backup = Path(args.backup_root).resolve()
            if backup == repo or backup.is_relative_to(repo):
                raise RuntimeError('Backup root must be outside the checkout')
            branch = git(repo, 'symbolic-ref', '--short', 'HEAD')
            if not branch.startswith('codex/'):
                raise RuntimeError('Use an approved codex/ task branch before starting')
            session = dict(id=uuid.uuid4().hex, owner=args.owner, repo=str(repo),
                           branch=branch, backup_root=str(backup),
                           remote=git(repo, 'remote', 'get-url', '--push', 'origin'))
            write_json(lock, session)
            print('Session ID:', session['id'], flush=True)
            snap = snapshot(repo, backup / session['id'] / 'start')
            print('LOCAL_BACKUP_VERIFIED', snap, flush=True)
            git(repo, 'fetch', 'origin')
            if git(repo, 'status', '--porcelain=v1', '-uall'):
                raise RuntimeError('Local changes preserved; reconcile before editing')
            remote = git(repo, 'ls-remote', '--heads', 'origin', 'refs/heads/' + branch)
            if remote and remote.split()[0] != git(repo, 'rev-parse', 'HEAD'):
                raise RuntimeError('Remote differs; review before proceeding')
            print('READY; keep session ID. Reserve final 20% for verification and handoff.')
        else:
            session = json.loads(lock.read_text())
            if args.action == 'auto-checkpoint':
                args.session = session['id']
            if args.session != session['id'] or str(repo) != session['repo']:
                raise RuntimeError('Session ID or checkout mismatch')
            if git(repo, 'symbolic-ref', '--short', 'HEAD') != session['branch']:
                raise RuntimeError('Branch changed during session')
            snap = snapshot(repo, Path(session['backup_root']) / session['id'] / uuid.uuid4().hex)
            print('LOCAL_BACKUP_VERIFIED', snap, flush=True)
            if args.action in ('checkpoint', 'auto-checkpoint'):
                return
            if git(repo, 'remote', 'get-url', '--push', 'origin') != session['remote']:
                raise RuntimeError('Push destination changed; review before publishing')
            if not args.reviewed_head or not args.validation or not args.handoff:
                raise RuntimeError('finish requires --reviewed-head, --validation, --handoff')
            head = git(repo, 'rev-parse', 'HEAD')
            if args.reviewed_head != head or git(repo, 'status', '--porcelain=v1', '-uall'):
                raise RuntimeError('Commit reviewed files first; exact clean HEAD required')
            git(repo, 'diff', '--check', head + '^', head)
            branch = session['branch']
            git(repo, 'push', 'origin', head + ':refs/heads/' + branch)
            remote = git(repo, 'ls-remote', '--heads', 'origin', 'refs/heads/' + branch)
            if not remote or remote.split()[0] != head:
                raise RuntimeError('Remote commit verification failed')
            if git(repo, 'rev-parse', 'HEAD') != head or git(repo, 'status', '--porcelain=v1', '-uall'):
                raise RuntimeError('Work changed during push; session remains open')
            write_json(Path(snap) / 'completion.json', dict(
                head=head, validation=args.validation, handoff=args.handoff,
                status='SYNCED', evidence='validation and handoff supplied by operator'))
            lock.rename(common / ('work-bridge-completed-' + session['id'] + '.json'))
            print('SYNCED', head)
    finally:
        guard.unlink()  # Own transient mutex only; snapshots and session records retained.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['start', 'status', 'checkpoint', 'auto-checkpoint', 'finish'])
    parser.add_argument('--repo', default='.')
    for option in ['backup-root', 'owner', 'session', 'reviewed-head', 'validation', 'handoff']:
        parser.add_argument('--' + option)
    try:
        run(parser.parse_args())
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        print('BLOCKED:', str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
