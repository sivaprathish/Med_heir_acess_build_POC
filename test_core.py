import unittest, copy, tempfile
from datetime import date
from core import *
class Tests(unittest.TestCase):
 def setUp(self): self.db=load()
 def test_seed(self):
  self.assertEqual(validate(self.db),[])
  rows,_,warnings=flatten(self.db,'1','2026-09-23'); self.assertEqual(len(rows),1); self.assertEqual(warnings,[])
 def test_overlap(self):
  r=dict(self.db['node_relationships'][0]); r['relationship_id']='999'; self.db['node_relationships'].append(r)
  self.assertTrue(any('overlapping' in e for e in validate(self.db)))
 def test_wrong_type(self):
  self.db['node_relationships'][1]['parent']='0'; self.assertTrue(validate(self.db))
 def test_missing_node(self):
  self.db['node_relationships'][0]['child']='99999'; self.assertTrue(validate(self.db))
 def test_move_boundary(self):
  new=dict(node_id='99999',node_type_id='11',node_name='Demo alternate area'); self.db['nodes'].append(new)
  self.db['node_relationships'].append(dict(relationship_id='99',hier_id='1',level='1',parent='0',child='99999',start='2026-01-01',end=''))
  move(self.db,'2','99999','2026-10-01'); self.assertEqual(validate(self.db),[])
  before=flatten(self.db,'1','2026-09-30')[0]; after=flatten(self.db,'1','2026-10-01')[0]
  self.assertEqual(before[0]['area_name'],'Americas'); self.assertEqual(after[0]['area_name'],'Demo alternate area')
 def test_rename(self):
  n=next(n for n in self.db['nodes'] if n['node_name']=='Americas'); n['node_name']='New Americas'
  self.assertEqual(flatten(self.db,'1','2026-09-23')[0][0]['area_name'],'New Americas')
 def test_incomplete(self):
  self.db['node_relationships'].pop(); rows,_,warnings=flatten(self.db,'1','2026-09-23'); self.assertFalse(rows); self.assertTrue(warnings)
 def test_date(self):
  self.db['node_relationships'][0]['end']='2025-01-01'; self.assertTrue(validate(self.db))
 def test_roundtrip(self):
  with tempfile.TemporaryDirectory() as folder:
   for name,cols in SCHEMAS.items(): write_csv(Path(folder)/f'{name}.csv',self.db[name],cols)
   save(self.db,'nodes',folder); self.assertEqual(load(folder),self.db)
if __name__=='__main__': unittest.main()
