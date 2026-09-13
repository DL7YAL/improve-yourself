"""Integration checks using disposable local Git repositories, no GitHub writes."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/dev/work_bridge.py'


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.remote = self.root / 'remote.git'
        self.backup = self.root / 'backups'
        self.call('git', 'init', '--bare', str(self.remote))
        self.call('git', 'init', '-b', 'codex/test', str(self.repo))
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        (self.repo / 'data.txt').write_text('original')
        self.git('add', 'data.txt')
        self.git('commit', '-m', 'initial')
        self.git('remote', 'add', 'origin', str(self.remote))
        self.git('push', '-u', 'origin', 'codex/test')

    def call(self, *args):
        return subprocess.check_output(args, stderr=subprocess.PIPE).decode().strip()

    def git(self, *args):
        return self.call('git', '-C', str(self.repo), *args)

    def bridge(self, action, *args):
        return subprocess.run([sys.executable, str(SCRIPT), action, '--repo',
                               str(self.repo), *args], capture_output=True, text=True)

    def start(self):
        result = self.bridge('start', '--owner', 'one', '--backup-root', str(self.backup))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads((self.repo / '.git/work-bridge-session.json').read_text())['id']

    def finish(self, sid):
        return self.bridge('finish', '--session', sid, '--reviewed-head',
                           self.git('rev-parse', 'HEAD'), '--validation', 'unit checks',
                           '--handoff', 'test handoff')

    def test_lock_snapshot_push_and_restore(self):
        sid = self.start()
        self.assertNotEqual(self.bridge('start', '--owner', 'two', '--backup-root',
                                       str(self.backup)).returncode, 0)
        (self.repo / 'data.txt').write_text('updated')
        self.assertEqual(self.bridge('checkpoint', '--session', sid).returncode, 0)
        self.assertNotEqual(self.finish(sid).returncode, 0)  # dirty finish blocked
        self.git('add', 'data.txt')
        self.git('commit', '-m', 'updated')
        result = self.finish(sid)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('SYNCED', result.stdout)
        self.assertFalse((self.repo / '.git/work-bridge-session.json').exists())
        initial = self.backup / sid / 'start'
        restored = self.root / 'restored'
        self.call('git', 'clone', '-b', 'codex/test', str(initial / 'history.bundle'), str(restored))
        self.assertEqual((restored / 'data.txt').read_text(), 'original')
        with zipfile.ZipFile(initial / 'working.zip') as z:
            self.assertEqual(z.read('data.txt'), b'original')

    def test_failed_push_preserves_session_and_backup(self):
        sid = self.start()
        (self.repo / 'data.txt').write_text('next')
        self.git('add', 'data.txt')
        self.git('commit', '-m', 'next')
        other = self.root / 'other'
        self.call('git', 'clone', '-b', 'codex/test', str(self.remote), str(other))
        self.call('git', '-C', str(other), 'config', 'user.name', 'Other')
        self.call('git', '-C', str(other), 'config', 'user.email', 'other@example.invalid')
        self.call('git', '-C', str(other), 'commit', '--allow-empty', '-m', 'concurrent work')
        self.call('git', '-C', str(other), 'push')
        result = self.finish(sid)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('LOCAL_BACKUP_VERIFIED', result.stdout)
        self.assertTrue((self.repo / '.git/work-bridge-session.json').exists())

    def test_wrong_session_and_inside_backup_rejected(self):
        self.assertNotEqual(self.bridge('start', '--owner', 'one', '--backup-root',
                                       str(self.repo / 'backup')).returncode, 0)
        self.start()
        self.assertNotEqual(self.bridge('checkpoint', '--session', 'wrong').returncode, 0)


if __name__ == '__main__':
    unittest.main()
