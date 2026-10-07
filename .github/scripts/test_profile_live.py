import datetime as dt
import unittest
from unittest.mock import patch
import tempfile
import os
from types import SimpleNamespace
from pathlib import Path
import xml.etree.ElementTree as ET
import profile_live as profile


def issue(number, word, user='visitor', state='open', **extra):
    return dict(number=number, title='[Research word]', body='### Research topic\n\n'+word,
                user={'login': user}, state=state, **extra)


class ProfileTests(unittest.TestCase):
    def test_one_vote_per_account_and_withdrawal(self):
        counts, users = profile.topics([issue(1, 'Catalysis'), issue(2, 'Materials'),
            issue(3, 'Lab Safety', 'other'), issue(4, 'RAG', 'closed', 'closed')])
        self.assertEqual(dict(counts), {'materials': 1, 'lab safety': 1})
        self.assertEqual(users, 2)

    def test_invalid_inputs_and_pull_requests_do_not_count(self):
        invalid = ['<script>alert(1)</script>', '$(whoami)', 'x'*31, '', 'a\nb']
        # Multiline forms contribute only their first input line; shell/HTML syntax is rejected.
        self.assertEqual(profile.topics([issue(i, w) for i, w in enumerate(invalid[:4])]), ({}, 0))
        self.assertEqual(profile.topics([issue(1, 'Catalysis', pull_request={})]), ({}, 0))
        self.assertEqual(profile.topics([issue(1, 'Catalysis', pull_request={'url': 'x'})]), ({}, 0))

    def test_case_insensitive_votes_and_unicode(self):
        counts, users = profile.topics([issue(1, 'Catalysis', 'a'), issue(2, 'CATALYSIS', 'b'), issue(3, '催化剂发现', 'c')])
        self.assertEqual(counts['catalysis'], 2)
        self.assertEqual(users, 3)

    def test_empty_cloud_never_claims_participants(self):
        result = profile.cloud([], 'en')
        self.assertIn('0 participants', result)
        self.assertIn('Example words', result)

    def test_shuffle_does_not_change_vote_counts(self):
        votes = [issue(1, 'Materials', 'a'), issue(2, 'Catalysis', 'b'), issue(3, 'Lab Safety', 'c')]
        shuffled = votes + [dict(number=10, title='[Shuffle research cloud]', state='open')]
        self.assertEqual(profile.topics(votes), profile.topics(shuffled))

    def test_leap_year_denominator(self):
        now = dt.datetime(2024, 7, 2, tzinfo=dt.timezone.utc)
        self.assertIn('50.0%', profile.progress(now, 'en'))

    def test_bilingual_svg_and_release_distinction(self):
        files = profile.render([], [('AdsMind', None), ('catdt-gs', None)], dt.datetime(2026, 10, 7, tzinfo=dt.timezone.utc))
        self.assertEqual(len(files), 6)
        for content in files.values():
            ET.fromstring(content)
        self.assertIn('No published GitHub release', files['updates-en.svg'])
        for version in ['CatDT v1', 'CatDT v2', 'AdsMind v1']:
            self.assertIn(version, files['updates-en.svg'])

    def test_cloud_packing_long_unicode_has_no_overlap(self):
        words = ['催化剂材料科学自动发现' * 2 + str(i) for i in range(18)]
        counts = {word: i+1 for i, word in enumerate(words)}
        layout = profile.cloud_layout(words, counts, 17)
        self.assertEqual(len(layout), 18)
        for index, (_, x, y, width, size) in enumerate(layout):
            self.assertGreaterEqual(x, 24)
            self.assertLessEqual(x+width, 736)
            for _, px, py, pw, ps in layout[:index]:
                self.assertTrue(x+width+8<px or px+pw+8<x or y+size*1.35+6<py or py+ps*1.35+6<y)

    def test_cloud_scale_and_shuffle_geometry(self):
        words = ['Catalysis', 'Materials', 'Robotics']
        counts = {'Catalysis': 9, 'Materials': 2, 'Robotics': 1}
        first = profile.cloud_layout(words, counts, 0)
        second = profile.cloud_layout(words, counts, 42)
        sizes = {word: size for word, _, _, _, size in first}
        self.assertGreater(sizes['Catalysis'], sizes['Robotics'])
        self.assertNotEqual(first, second)

    def test_release_summary_uses_original_notes(self):
        self.assertEqual(profile.release_summary({'body': '## Changes\n\n* Added [memory](https://example.com) caching'}), 'Added memory caching')
        self.assertEqual(profile.release_summary({'body': ''}), '')

    def test_latest_closed_vote_does_not_restore_old_vote(self):
        old = issue(1, 'Catalysis')
        latest = issue(2, 'Materials', state='closed')
        self.assertEqual(profile.topics([old, latest]), ({}, 0))
        latest['state'] = 'open'
        self.assertEqual(profile.topics([old, latest]), ({'materials': 1}, 1))
        latest['body'] = '### Research topic\n\nLab Safety'
        self.assertEqual(profile.topics([old, latest]), ({'lab safety': 1}, 1))

    def test_casefold_expansion_stays_inside_canvas(self):
        counts, _ = profile.topics([issue(1, 'ΐ'*30)])
        for _, x, _, width, size in profile.cloud_layout(list(counts), counts, 0):
            self.assertGreater(size, 0)
            self.assertGreaterEqual(x, 24)
            self.assertLessEqual(x+width, 736)

    def test_release_summary_preserves_numbers_and_identifiers(self):
        for original in ['98.8% success rate', '1.2.0 improves catdt_gs', '-0.5 eV change']:
            self.assertEqual(profile.release_summary({'body': original}), original)
        self.assertEqual(profile.release_summary({'body': '1. Added `catdt_gs`'}), 'Added catdt_gs')

    def test_expanded_unicode_fallback_is_bounded(self):
        word = ('ΐ'*30).casefold()
        for _, x, _, width, size in profile.cloud_layout([word], {word: 1}, 0):
            self.assertGreater(size, 0)
            self.assertGreaterEqual(x, 24)
            self.assertLessEqual(x+width, 736)

    def test_main_fetches_closed_issues_for_withdrawal(self):
        calls = []
        def api(path):
            calls.append(path)
            if '/issues?' in path:
                return [issue(1, 'Catalysis'), issue(2, 'Materials', state='closed')]
            if path.endswith('/releases/latest'):
                return {'body': '98.8% success', 'tag_name': 'v1', 'published_at': '2026-10-08T00:00:00Z', 'html_url': 'https://github.com/example/releases/tag/v1'}
            if '/repos?' in path:
                return []
            return {'followers': 0}
        with tempfile.TemporaryDirectory() as directory, patch.object(profile, 'ROOT', Path(directory)), patch.object(profile, 'api', side_effect=api), patch('profile_extras.build', return_value={}), patch('profile_collection.build', return_value={}):
            profile.main()
            cloud = (Path(directory)/'assets/live/community-en.svg').read_text(encoding='utf-8')
            self.assertIn('0 participants', cloud)
        self.assertTrue(any('/issues?state=all&' in path for path in calls))

    def test_metrics_excludes_fork_stars(self):
        result = profile.metrics({'followers': 48}, [{'fork': False, 'stargazers_count': 7}, {'fork': True, 'stargazers_count': 100}], 'en', dt.datetime.now(dt.timezone.utc))
        self.assertIn('>7</text>', result)
        self.assertNotIn('>107</text>', result)
        self.assertIn('<animate ', result)
        ET.fromstring(result)

    def test_publisher_creates_nested_history_files(self):
        calls = []
        def git_run(arguments, **kwargs):
            calls.append(arguments)
            if arguments[:2] == ['git', 'add']:
                self.assertEqual((Path(kwargs['cwd'])/'history/2026-Q4-en.svg').read_text(), '<svg/>')
            output = 'history/2026-Q4-en.svg' if arguments[:3] == ['git', 'diff', '--cached'] else ''
            return SimpleNamespace(returncode=0, stdout=output, stderr='')
        with patch.dict(os.environ, {'GH_TOKEN': 'test-token'}), patch.object(profile, 'api', return_value={}), patch.object(profile.subprocess, 'run', side_effect=git_run):
            profile.publish({'history/2026-Q4-en.svg': '<svg/>'})
        self.assertTrue(any(args[:2] == ['git', 'push'] for args in calls))


if __name__ == '__main__':
    unittest.main()
