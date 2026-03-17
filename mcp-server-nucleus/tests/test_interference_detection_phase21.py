import json
import unittest
from pathlib import Path
import shutil
import tempfile
from mcp_server_nucleus.runtime.context_graph import ContextGraph
from mcp_server_nucleus.runtime.dsor import DecisionLedger

class TestInterferenceDetection(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.brain_path = self.test_dir / ".brain"
        self.brain_path.mkdir()
        (self.brain_path / "ledger").mkdir()
        
        self.graph = ContextGraph(self.brain_path)
        self.ledger = DecisionLedger(self.brain_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_basic_interference(self):
        # 1. Record Decision A related to File X
        dec_a_id = "DEC-A"
        self.graph.link_nodes(dec_a_id, "file:///src/main.py", "reads", weight=1.0)
        
        # 2. Record Decision B related to File X
        dec_b_id = "DEC-B"
        self.graph.link_nodes(dec_b_id, "file:///src/main.py", "modifies", weight=0.8)
        
        # 3. Check interference for A
        interferences = self.graph.check_interference(dec_a_id)
        
        self.assertEqual(len(interferences), 1)
        self.assertEqual(interferences[0]["interfering_node_id"], dec_b_id)
        self.assertEqual(interferences[0]["shared_context_node"], "file:///src/main.py")
        self.assertEqual(interferences[0]["weight"], 0.8)

    def test_no_interference(self):
        # A relates to X, B relates to Y
        self.graph.link_nodes("DEC-A", "file:///src/a.py", "reads")
        self.graph.link_nodes("DEC-B", "file:///src/b.py", "modifies")
        
        interferences = self.graph.check_interference("DEC-A")
        self.assertEqual(len(interferences), 0)

    def test_multiple_interferences(self):
        # A relates to X
        # B relates to X
        # C relates to X
        self.graph.link_nodes("DEC-A", "file:///shared.py", "reads")
        self.graph.link_nodes("DEC-B", "file:///shared.py", "writes")
        self.graph.link_nodes("DEC-C", "file:///shared.py", "imports")
        
        interf_a = self.graph.check_interference("DEC-A")
        self.assertEqual(len(interf_a), 2)
        
        interfering_ids = [i["interfering_node_id"] for i in interf_a]
        self.assertIn("DEC-B", interfering_ids)
        self.assertIn("DEC-C", interfering_ids)

    def test_bidirectional_interference(self):
        # A -> X, X -> B (using link_nodes logic which handles both ways)
        # The current implementation of check_interference uses both source_id and target_id
        self.graph.link_nodes("DEC-A", "file:///data.json", "consumes")
        self.graph.link_nodes("file:///data.json", "DEC-B", "produced_by")
        
        interf_a = self.graph.check_interference("DEC-A")
        self.assertEqual(len(interf_a), 1)
        self.assertEqual(interf_a[0]["interfering_node_id"], "DEC-B")

if __name__ == "__main__":
    unittest.main()
