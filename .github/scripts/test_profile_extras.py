import datetime as dt
import json
import io
import tempfile
from pathlib import Path
from unittest.mock import patch
import unittest
import urllib.error
import xml.etree.ElementTree as ET

import profile_extras as extras
import profile_live as profile


def issue(number=1, word='Catalysis', state='open'):
    return {'number': number, 'title': '[Research word]', 'body': '### Research topic\n\n'+word,
            'state': state, 'user': {'login': 'visitor'}}


class ExtrasTests(unittest.TestCase):
    def test_notes_skip_maintenance_removed_and_hidden_files(self):
        def api(path):
            if '/commits?' in path:
                return [{'sha': 'new', 'commit': {'committer': {'date': '2026-10-08T00:00:00Z'}}},
                        {'sha': 'old', 'commit': {'committer': {'date': '2026-10-07T00:00:00Z'}}}]
            if path.endswith('/new'):
                return {'files': [{'filename': 'README_EN.md', 'status': 'modified'},
                                  {'filename': '.obsidian/settings.md', 'status': 'modified'},
                                  {'filename': 'Deleted.md', 'status': 'removed'}]}
            return {'files': [{'filename': '课程/微调笔记.md', 'status': 'modified'}]}
        with patch.object(profile, 'api', side_effect=api):
            notes = extras.latest_notes(['owner/notes'])
        self.assertEqual(notes[0]['title'], '微调笔记')
        self.assertEqual(notes[0]['sha'], 'old')
        self.assertIn('/blob/old/', notes[0]['url'])
        self.assertIn('%E8', notes[0]['url'])

    def test_notes_sort_dates_and_limit_one_per_repository(self):
        def api(path):
            repo = path.split('/')[2]
            if '/commits?' in path:
                return [{'sha': repo, 'commit': {'committer': {'date': f'2026-10-0{repo[-1]}T00:00:00Z'}}}]
            return {'files': [{'filename': 'A.md', 'status': 'added'}, {'filename': 'B.md', 'status': 'added'}]}
        with patch.object(profile, 'api', side_effect=api):
            notes = extras.latest_notes(['owner/repo1', 'owner/repo2', 'owner/repo3', 'owner/repo4'])
        self.assertEqual([n['repository'] for n in notes], ['owner/repo4', 'owner/repo3', 'owner/repo2'])

    def test_examples_never_enter_history(self):
        self.assertEqual(extras.update_history([], [], dt.datetime(2026, 10, 8, tzinfo=dt.timezone.utc)), [])
        self.assertIn('example words are never archived', extras.history_card([], 'en'))

    def test_quarter_snapshot_is_stable_and_withdrawal_clears_current(self):
        now = dt.datetime(2026, 10, 8, tzinfo=dt.timezone.utc)
        history = extras.update_history([], [issue()], now)
        self.assertEqual(history[0]['period'], '2026-Q4')
        self.assertNotIn('visitor', json.dumps(history))
        self.assertEqual(extras.update_history(history, [issue()], now+dt.timedelta(days=1)), history)
        self.assertEqual(extras.update_history(history, [issue(state='closed')], now), [])
        next_quarter = now.replace(year=2027, month=1)
        self.assertEqual(extras.update_history(history, [], next_quarter), history)

    def test_history_retains_eight_quarters(self):
        history = []
        for i in range(10):
            now = dt.datetime(2024+i//4, 1+(i%4)*3, 1, tzinfo=dt.timezone.utc)
            history = extras.update_history(history, [issue()], now)
        self.assertEqual(len(history), 8)
        self.assertEqual(history[0]['period'], '2024-Q3')

    def test_ready_activity_uses_seconds_and_separate_denominators(self):
        data = {'status': 'ready', 'start': '2026-10-01', 'end': '2026-10-07', 'timezone': 'UTC',
                'languages': [{'name': 'Python', 'total_seconds': 3600}, {'name': 'Rust', 'total_seconds': 3600}],
                'editors': [{'name': 'VS Code', 'total_seconds': 7200}]}
        card = extras.activity_card(data, 'en')
        self.assertIn('1.0 h · 50%', card)
        self.assertIn('2.0 h · 100%', card)
        self.assertIn('<animate ', card)
        ET.fromstring(card)

    def test_unconnected_activity_makes_no_network_request_or_hour_claim(self):
        with patch('urllib.request.urlopen') as request:
            result = extras.fetch_activity(None)
        request.assert_not_called()
        card = extras.activity_card(result, 'en')
        self.assertIn('Awaiting public WakaTime data', card)
        self.assertNotIn('0.0 h', card)
        with self.assertRaises(ValueError):
            extras.fetch_activity('https://example.com/private')

    def test_public_activity_request_never_sends_github_credentials(self):
        payload = {'data': {'is_up_to_date': False}}
        with patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(payload).encode())) as request:
            result = extras.fetch_activity('public-user')
        self.assertEqual(result['status'], 'pending')
        sent = request.call_args.args[0]
        self.assertEqual(sent.full_url, 'https://api.wakatime.com/api/v1/users/public-user/stats/last_7_days')
        self.assertIsNone(sent.get_header('Authorization'))

    def test_notes_failure_retains_last_successful_snapshot(self):
        note = {'repository': 'owner/notes', 'path': 'note.md', 'title': 'Verified note',
                'updated_at': '2026-10-01T00:00:00Z', 'sha': 'abc', 'url': 'https://github.com/owner/notes/blob/abc/note.md'}
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory)/'.github/profile-widgets.json'
            config.parent.mkdir()
            config.write_text(json.dumps({'note_repositories': ['owner/notes'], 'wakatime_username': None}))
            with patch.object(profile, 'ROOT', Path(directory)), patch.object(extras, 'load_state', return_value={'notes': [note]}), patch.object(extras, 'latest_notes', side_effect=urllib.error.URLError('offline')):
                files = extras.build([], dt.datetime(2026, 10, 8, tzinfo=dt.timezone.utc))
        self.assertEqual(json.loads(files['extras-state.json'])['notes'], [note])
        self.assertIn('Last successful snapshot retained', files['notes-en.svg'])

    def test_build_outputs_valid_bilingual_assets_and_history_paths(self):
        now = dt.datetime(2026, 10, 8, tzinfo=dt.timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory)/'.github/profile-widgets.json'
            config.parent.mkdir()
            config.write_text(json.dumps({'note_repositories': [], 'wakatime_username': None}))
            with patch.object(profile, 'ROOT', Path(directory)), patch.object(extras, 'load_state', return_value={}):
                files = extras.build([issue()], now)
        for name, content in files.items():
            if name.endswith('.svg'):
                ET.fromstring(content)
        self.assertIn('history/2026-Q4-cn.svg', files)
        self.assertIn('notes.md', files)
        self.assertIn('history.md', files)


if __name__ == '__main__':
    unittest.main()
