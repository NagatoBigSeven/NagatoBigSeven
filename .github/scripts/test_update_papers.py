import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from xml.sax.saxutils import escape
import update_papers as p


def feed(ids=p.CONFIRMED_IDS, author=p.AUTHOR, title="Paper: title"):
    entries = [f'<entry><id>http://arxiv.org/abs/{paper_id}v2</id>'
               f'<title>{escape(title)}</title><published>2026-06-01T00:00:00Z</published>'
               f'<author><name>{escape(author)}</name></author></entry>' for paper_id in ids]
    return ('<feed xmlns="http://www.w3.org/2005/Atom">' + ''.join(entries) + '</feed>').encode()


class PaperTests(unittest.TestCase):
    def test_rejects_same_name_unconfirmed_paper(self):
        with self.assertRaises(ValueError):
            p.parse_feed(feed((*p.CONFIRMED_IDS, "2505.04488"), title="Language model agent chemistry"))

    def test_missing_empty_duplicate_and_wrong_author_fail(self):
        for data in (feed(()), feed(p.CONFIRMED_IDS[:2]),
                     feed((*p.CONFIRMED_IDS, p.CONFIRMED_IDS[0])), feed(author="Other Author"), b'<error/>'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                p.parse_feed(data)

    def test_secure_request_exact_ids(self):
        with patch.object(p.urllib.request, 'urlopen') as open_url:
            open_url.return_value.__enter__.return_value.read.return_value = feed()
            self.assertEqual(len(p.fetch_papers()), 3)
            request = open_url.call_args.args[0]
            self.assertTrue(request.full_url.startswith('https://export.arxiv.org/'))
            self.assertNotIn('search_query', request.full_url)
            self.assertNotIn('context', open_url.call_args.kwargs)

    def docs(self, directory, bad_cn=False):
        originals = {}
        for name, status in [('README.md', 'Under review'), ('README_CN.md', '审稿中')]:
            text = f'Before\n{p.START}\n| # | Paper | Status |\n|:-:|:------|:------|\n'
            text += f'| 1 | Old | {status} · [arXiv:2606.19152](https://arxiv.org/abs/2606.19152) |\n'
            text += f'{p.END}\nAfter\n'
            if bad_cn and name == 'README_CN.md':
                text = text.replace(p.END, '')
            path = Path(directory) / name
            path.write_text(text, encoding='utf-8')
            originals[path] = path.read_bytes()
        return originals

    def test_failure_leaves_both_readmes_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            originals = self.docs(directory)
            with patch.object(p, 'fetch_papers', side_effect=ValueError('incomplete')), self.assertRaises(ValueError):
                p.update_readmes(directory)
            for path, data in originals.items():
                self.assertEqual(path.read_bytes(), data)

    def test_bad_markers_prevent_any_fetch_or_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            originals = self.docs(directory, bad_cn=True)
            with patch.object(p, 'fetch_papers') as fetch, self.assertRaises(ValueError):
                p.update_readmes(directory)
            fetch.assert_not_called()
            for path, data in originals.items():
                self.assertEqual(path.read_bytes(), data)
        for text in (p.END + p.START, p.START + p.START + p.END):
            with self.assertRaises(ValueError):
                p.paper_block(text)

    def test_single_snapshot_bilingual_statuses_and_idempotence(self):
        with tempfile.TemporaryDirectory() as directory:
            self.docs(directory)
            papers = p.parse_feed(feed(title='Paper: [link] | <img>'))
            with patch.object(p, 'fetch_papers', return_value=papers) as fetch:
                p.update_readmes(directory)
                fetch.assert_called_once()
                first = {path: path.read_bytes() for path in Path(directory).iterdir()}
                p.update_readmes(directory)
            for path, data in first.items():
                self.assertEqual(path.read_bytes(), data)
                text = path.read_text(encoding='utf-8')
                self.assertTrue(text.startswith('Before\n'))
                self.assertTrue(text.endswith('\nAfter\n'))
                self.assertIn('\\|', text)
                self.assertNotIn('<img>', text)
                self.assertIn('审稿中' if path.name == 'README_CN.md' else 'Under review', text)

    def test_cli_reports_failure(self):
        with patch.object(p, 'update_readmes', side_effect=OSError('offline')):
            self.assertEqual(p.main(), 1)


if __name__ == '__main__':
    unittest.main()
