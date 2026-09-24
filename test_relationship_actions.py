import unittest
from copy import deepcopy
from relationship_actions import add_relationship, modify_relationship, end_relationship

class RelationshipTests(unittest.TestCase):
    def setUp(self):
        self.db={
            'node_types':[{'node_type_id':str(i),'node_type_name':n} for i,n in [(0,'Root'),(11,'Area'),(12,'Region')]],
            'nodes':[{'node_id':str(i),'node_type_id':str(t),'node_name':n} for i,t,n in [(0,0,'Root'),(1,11,'A'),(2,11,'B'),(3,12,'Region')]],
            'hierarchies':[dict(hier_id='1',hier_desc='Test',active='Y')],
            'level_rules':[dict(hier_id='1',level='1',parent_node_type='0',child_node_type='11'),dict(hier_id='1',level='2',parent_node_type='11',child_node_type='12')],
            'node_relationships':[dict(relationship_id='1',hier_id='1',level='2',parent='1',child='3',start='2026-01-01',end='')]
        }
    def test_add(self):
        d=add_relationship(self.db,'1','1','0','1','2026-01-01')
        self.assertEqual(d['node_relationships'][-1]['end'],'')
        self.assertEqual(d['node_relationships'][-1]['relationship_id'],'2')
    def test_modify(self):
        d=modify_relationship(self.db,'1','2','2026-02-01'); old,new=d['node_relationships']
        self.assertEqual(old['relationship_id'],'1'); self.assertEqual(old['end'],'2026-02-01')
        self.assertEqual(new['relationship_id'],'2'); self.assertEqual(new['start'],old['end']); self.assertEqual(new['end'],''); self.assertEqual(new['child'],'3')
        self.assertEqual(self.db['node_relationships'][0]['end'],'')
    def test_end(self):
        d=end_relationship(self.db,'1','2026-02-01')
        self.assertEqual(len(d['node_relationships']),1); self.assertEqual(d['node_relationships'][0]['relationship_id'],'1')
        self.assertEqual(d['node_relationships'][0]['end'],'2026-02-01')
    def test_failed_modify_unchanged(self):
        before=deepcopy(self.db)
        with self.assertRaises(ValueError): modify_relationship(self.db,'1','0','2026-02-01')
        self.assertEqual(self.db,before)
    def test_overlap_rejected(self):
        with self.assertRaises(ValueError): add_relationship(self.db,'1','2','2','3','2026-03-01')
    def test_same_day_rejected(self):
        with self.assertRaises(ValueError): end_relationship(self.db,'1','2026-01-01')
    def test_closed_rejected(self):
        d=end_relationship(self.db,'1','2026-02-01')
        with self.assertRaises(ValueError): end_relationship(d,'1','2026-03-01')
    def test_inactive_rejected(self):
        self.db['hierarchies'][0]['active']='N'
        with self.assertRaises(ValueError): modify_relationship(self.db,'1','2','2026-02-01')
if __name__=='__main__': unittest.main()
