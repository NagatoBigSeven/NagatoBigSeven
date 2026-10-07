import unittest
import profile_collection as c
class CollectionTests(unittest.TestCase):
 def event(self, action='opened', merged=False, repo='owner/repo'):
  return {'type':'PullRequestEvent','repo':{'name':repo},'created_at':'2026-10-08T00:00:00Z','actor':{'login':'human'},'payload':{'action':action,'pull_request':{'merged':merged,'title':'Fix <layout>','html_url':'https://github.com/owner/repo/pull/1'}}}
 def test_closed_unmerged_excluded(self):
  self.assertEqual(c.meaningful([self.event('closed')]),[])
 def test_merged_kept_and_deduplicated(self):
  self.assertEqual(len(c.meaningful([self.event('closed',True),self.event()])),1)
 def test_profile_and_bots_excluded(self):
  bot=self.event();bot['actor']['login']='update[bot]'
  self.assertEqual(c.meaningful([bot,self.event(repo=c.p.REPO)]),[])
 def test_html_escaped(self):
  text=c.directory([{'language':'<x>','url':'https://github.com/a/b','name':'a/<b>','description':'<script>'}],[],[])
  self.assertNotIn('<script>',text)
 def test_empty_svg_valid(self):
  import datetime,xml.etree.ElementTree as ET
  ET.fromstring(c.card('Title',[], 'en',datetime.datetime.now(datetime.timezone.utc)))
if __name__=='__main__': unittest.main()
