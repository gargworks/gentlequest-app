"""
Stress Test Suite for CRDTTaskStore
Verifies: Zero data loss, conflict resolution, JSON serialization, scale matrix

Test Strategy:
- Single-threaded writes: 100 tasks sequential
- Concurrent writes: 1000 tasks, 100 threads
- Conflict resolution: LWW + vector clocks
- JSON export/import: Idempotency
- Performance: Meets scale matrix (1→100→10K)

Author: NOP V3 - January 2026
"""

import unittest
import threading
import time
import json
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Set

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nop_core.crdt_task_store import CRDTTaskStore


class TestCRDTTaskStoreBasic(unittest.TestCase):
    """Basic functionality tests."""
    
    def setUp(self):
        self.store = CRDTTaskStore(replica_id="test_replica")
    
    def test_add_task(self):
        """Test adding a single task."""
        task = {
            "id": "task_001",
            "title": "Test task",
            "status": "PENDING",
            "tier": "T1_PLANNING",
            "created_at": int(time.time() * 1000),
        }
        
        result = self.store.add_task(task)
        
        # Verify CRDT metadata added
        assert result["id"] == "task_001"
        assert result["updated_at"] is not None
        assert result["replica_id"] == "test_replica"
        assert result["vector_clock"] is not None
        assert result["vector_clock"]["test_replica"] == 1
    
    def test_get_task(self):
        """Test retrieving a task."""
        task = {
            "id": "task_002",
            "title": "Retrieve test",
            "status": "PENDING",
            "tier": "T2_CODE",
            "created_at": int(time.time() * 1000),
        }
        
        self.store.add_task(task)
        retrieved = self.store.get_task("task_002")
        
        assert retrieved is not None
        assert retrieved["id"] == "task_002"
        assert retrieved["title"] == "Retrieve test"
    
    def test_update_task(self):
        """Test updating a task."""
        task = {
            "id": "task_003",
            "title": "Update test",
            "status": "PENDING",
            "tier": "T3_REVIEW",
            "created_at": int(time.time() * 1000),
        }
        
        self.store.add_task(task)
        original_timestamp = self.store.get_task("task_003")["updated_at"]
        
        time.sleep(0.01)  # Ensure timestamp difference
        
        updated = self.store.update_task("task_003", {"status": "IN_PROGRESS"})
        new_timestamp = updated["updated_at"]
        
        # LWW: New timestamp should be later
        assert new_timestamp > original_timestamp
        assert updated["status"] == "IN_PROGRESS"
    
    def test_delete_task(self):
        """Test deleting a task (tombstone)."""
        task = {
            "id": "task_004",
            "title": "Delete test",
            "status": "PENDING",
            "tier": "T4_DEPLOY",
            "created_at": int(time.time() * 1000),
        }
        
        self.store.add_task(task)
        assert self.store.get_task("task_004") is not None
        
        self.store.delete_task("task_004")
        
        assert self.store.get_task("task_004") is None
    
    def test_get_all_tasks(self):
        """Test retrieving all tasks."""
        tasks = [
            {
                "id": f"task_{i:03d}",
                "title": f"Task {i}",
                "status": "PENDING",
                "tier": "T1_PLANNING",
                "created_at": int(time.time() * 1000),
            }
            for i in range(10)
        ]
        
        for task in tasks:
            self.store.add_task(task)
        
        all_tasks = self.store.get_all_tasks()
        assert len(all_tasks) == 10
        
        # Should be sorted by updated_at descending
        timestamps = [t["updated_at"] for t in all_tasks]
        assert timestamps == sorted(timestamps, reverse=True)


class TestCRDTTaskStoreSerialize(unittest.TestCase):
    """JSON serialization and deserialization tests."""
    
    def setUp(self):
        self.store = CRDTTaskStore(replica_id="serialize_test")
    
    def test_to_json_basic(self):
        """Test exporting to JSON."""
        task = {
            "id": "task_json_001",
            "title": "JSON test",
            "status": "PENDING",
            "tier": "T1_PLANNING",
            "created_at": int(time.time() * 1000),
        }
        
        self.store.add_task(task)
        json_str = self.store.to_json()
        
        # Verify valid JSON
        data = json.loads(json_str)
        assert "tasks" in data
        assert "vector_clocks" in data
        assert len(data["tasks"]) == 1
    
    def test_from_json_basic(self):
        """Test importing from JSON."""
        task = {
            "id": "task_json_002",
            "title": "Import test",
            "status": "PENDING",
            "tier": "T2_CODE",
            "created_at": int(time.time() * 1000),
        }
        
        self.store.add_task(task)
        json_str = self.store.to_json()
        
        # Create new store and import
        new_store = CRDTTaskStore(replica_id="new_replica")
        new_store.from_json(json_str)
        
        # Verify data matches
        new_task = new_store.get_task("task_json_002")
        assert new_task is not None
        assert new_task["title"] == "Import test"
    
    def test_json_idempotency(self):
        """Test that export/import is idempotent."""
        tasks = [
            {
                "id": f"task_idem_{i:03d}",
                "title": f"Idempotent {i}",
                "status": "PENDING",
                "tier": "T1_PLANNING",
                "created_at": int(time.time() * 1000),
            }
            for i in range(5)
        ]
        
        for task in tasks:
            self.store.add_task(task)
        
        # Export, import, export again
        json1 = self.store.to_json()
        
        new_store = CRDTTaskStore(replica_id="test_replica")  # Use same replica_id
        new_store.from_json(json1)
        json2 = new_store.to_json()
        
        # JSONs should be identical
        data1 = json.loads(json1)
        data2 = json.loads(json2)
        
        assert len(data1["tasks"]) == len(data2["tasks"])
        assert data1["vector_clocks"] == data2["vector_clocks"]


class TestCRDTTaskStoreMerge(unittest.TestCase):
    """CRDT merge and conflict resolution tests."""
    
    def test_merge_new_tasks(self):
        """Test merging new tasks from remote."""
        store1 = CRDTTaskStore(replica_id="replica_1")
        store2 = CRDTTaskStore(replica_id="replica_2")
        
        task1 = {
            "id": "task_merge_001",
            "title": "Store 1 task",
            "status": "PENDING",
            "tier": "T1_PLANNING",
            "created_at": int(time.time() * 1000),
        }
        task2 = {
            "id": "task_merge_002",
            "title": "Store 2 task",
            "status": "IN_PROGRESS",
            "tier": "T2_CODE",
            "created_at": int(time.time() * 1000),
        }
        
        store1.add_task(task1)
        store2.add_task(task2)
        
        # Merge store2 into store1
        store1.merge(store2)
        
        # Both tasks should be in store1 now
        assert store1.get_task("task_merge_001") is not None
        assert store1.get_task("task_merge_002") is not None
        assert len(store1.get_all_tasks()) == 2
    
    def test_merge_lww_conflict_resolution(self):
        """Test LWW conflict resolution during merge."""
        store1 = CRDTTaskStore(replica_id="replica_1")
        store2 = CRDTTaskStore(replica_id="replica_2")
        
        # Same task ID, different updates
        task = {
            "id": "task_conflict_001",
            "title": "Original",
            "status": "PENDING",
            "tier": "T1_PLANNING",
            "created_at": int(time.time() * 1000),
        }
        
        store1.add_task(task)
        time.sleep(0.01)
        
        # In store2, update the task (later timestamp)
        store2.add_task(task)
        store2.update_task("task_conflict_001", {"status": "IN_PROGRESS", "title": "Updated"})
        
        # Merge - store2's newer timestamp should win
        store1.merge(store2)
        
        merged_task = store1.get_task("task_conflict_001")
        assert merged_task["status"] == "IN_PROGRESS"
        assert merged_task["title"] == "Updated"
    
    def test_merge_vector_clocks(self):
        """Test vector clock merge."""
        store1 = CRDTTaskStore(replica_id="replica_1")
        store2 = CRDTTaskStore(replica_id="replica_2")
        
        task = {
            "id": "task_vc_001",
            "title": "Vector clock test",
            "status": "PENDING",
            "tier": "T1_PLANNING",
            "created_at": int(time.time() * 1000),
        }
        
        store1.add_task(task)
        store2.add_task(task)
        
        # Merge and verify vector clocks merged
        store1.merge(store2)
        
        merged_task = store1.get_task("task_vc_001")
        vc = merged_task["vector_clock"]
        
        # Both replicas should be in vector clock
        assert "replica_1" in vc
        assert "replica_2" in vc
        assert vc["replica_1"] >= 1
        assert vc["replica_2"] >= 1


class TestCRDTTaskStoreStress(unittest.TestCase):
    """Stress tests for concurrent writes and scale matrix."""
    
    def test_sequential_100_writes(self):
        """Test 100 sequential writes - zero loss."""
        store = CRDTTaskStore(replica_id="stress_sequential")
        
        task_ids = set()
        for i in range(100):
            task = {
                "id": f"task_seq_{i:03d}",
                "title": f"Sequential {i}",
                "status": "PENDING",
                "tier": "T1_PLANNING",
                "created_at": int(time.time() * 1000),
            }
            store.add_task(task)
            task_ids.add(task["id"])
        
        # Verify zero loss
        all_tasks = store.get_all_tasks()
        retrieved_ids = {t["id"] for t in all_tasks}
        
        assert len(all_tasks) == 100, f"Expected 100 tasks, got {len(all_tasks)}"
        assert task_ids == retrieved_ids, "Task IDs don't match - data loss detected!"
    
    def test_concurrent_1000_writes(self):
        """
        CRITICAL STRESS TEST: 1000 concurrent writes - ZERO DATA LOSS
        
        This test validates the CRDT invariant:
        - Every write must be persisted
        - No duplicates
        - No data loss
        """
        store = CRDTTaskStore(replica_id="stress_concurrent")
        
        num_threads = 100
        writes_per_thread = 10
        total_writes = num_threads * writes_per_thread
        
        written_tasks: Set[str] = set()
        write_lock = threading.Lock()
        
        def write_task(thread_id: int, write_id: int) -> str:
            """Write a task and track it."""
            task_id = f"task_concurrent_{thread_id:03d}_{write_id:02d}"
            task = {
                "id": task_id,
                "title": f"Concurrent {thread_id}-{write_id}",
                "status": "PENDING",
                "tier": "T2_CODE",
                "created_at": int(time.time() * 1000),
                "assigned_to": f"agent_{thread_id % 4}",
            }
            
            # Write to store (thread-safe)
            store.add_task(task)
            
            # Track written task
            with write_lock:
                written_tasks.add(task_id)
            
            # Simulate network delay (0-5ms)
            time.sleep(0.001 * (thread_id % 5))
            
            return task_id
        
        # Execute concurrent writes
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(write_task, t, w)
                for t in range(num_threads)
                for w in range(writes_per_thread)
            ]
            
            completed = 0
            for future in as_completed(futures):
                future.result()
                completed += 1
        
        elapsed = time.time() - start_time
        
        # VERIFY: Zero data loss
        all_tasks = store.get_all_tasks()
        retrieved_ids = {t["id"] for t in all_tasks}
        
        print(f"\n🚀 STRESS TEST RESULTS:")
        print(f"  Total writes: {total_writes}")
        print(f"  Writes written: {len(written_tasks)}")
        print(f"  Writes retrieved: {len(retrieved_ids)}")
        print(f"  Elapsed time: {elapsed:.2f}s")
        print(f"  Throughput: {total_writes/elapsed:.0f} writes/sec")
        print(f"  Data loss: {total_writes - len(retrieved_ids)} tasks")
        
        # Critical assertions
        assert len(retrieved_ids) == total_writes, (
            f"ZERO LOSS VIOLATION: "
            f"Expected {total_writes} tasks, "
            f"got {len(retrieved_ids)} (lost {total_writes - len(retrieved_ids)})"
        )
        assert written_tasks == retrieved_ids, "Task ID mismatch - corruption detected!"
        assert len(set(t["id"] for t in all_tasks)) == total_writes, (
            "Duplicate task IDs detected!"
        )
    
    def test_concurrent_updates(self):
        """Test concurrent updates to same task - LWW resolves conflicts."""
        store = CRDTTaskStore(replica_id="update_stress")
        
        task = {
            "id": "task_update_concurrent",
            "title": "Update stress",
            "status": "PENDING",
            "tier": "T1_PLANNING",
            "created_at": int(time.time() * 1000),
        }
        store.add_task(task)
        
        num_threads = 10
        
        def concurrent_update(thread_id: int) -> None:
            """Update the same task from multiple threads."""
            for i in range(5):
                store.update_task("task_update_concurrent", {
                    "status": f"status_{thread_id}_{i}",
                    "assigned_to": f"agent_{thread_id}",
                })
                time.sleep(0.001)
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(concurrent_update, t) for t in range(num_threads)]
            for future in as_completed(futures):
                future.result()
        
        # Task should exist and have LWW-resolved state
        final_task = store.get_task("task_update_concurrent")
        assert final_task is not None
        assert "status_" in final_task["status"]  # Should have one of the concurrent statuses
        assert final_task["vector_clock"]["update_stress"] > 1


class TestCRDTTaskStoreScaleMatrix(unittest.TestCase):
    """Validate scale matrix requirements (1→100→10K)."""
    
    def test_scale_matrix_1_user(self):
        """1 user: <10MB memory, <1 write/sec throughput."""
        store = CRDTTaskStore(replica_id="scale_1")
        
        for i in range(100):
            task = {
                "id": f"task_1user_{i:03d}",
                "title": f"1-user task {i}",
                "status": "PENDING",
                "tier": "T1_PLANNING",
                "created_at": int(time.time() * 1000),
            }
            store.add_task(task)
        
        stats = store.get_stats()
        assert stats["total_tasks"] == 100
        assert stats["memory_estimate_kb"] < 1024 * 10  # <10MB
        print(f"\n1 User scale: {stats['memory_estimate_kb']:.1f}KB")
    
    def test_scale_matrix_100_users(self):
        """100 users: <100MB memory, 10-20 writes/sec throughput."""
        store = CRDTTaskStore(replica_id="scale_100")
        
        start = time.time()
        for i in range(1000):
            task = {
                "id": f"task_100users_{i:04d}",
                "title": f"100-user task {i}",
                "status": "PENDING" if i % 2 == 0 else "IN_PROGRESS",
                "tier": ["T1_PLANNING", "T2_CODE", "T3_REVIEW", "T4_DEPLOY"][i % 4],
                "created_at": int(time.time() * 1000),
                "assigned_to": f"agent_{i % 10}",
            }
            store.add_task(task)
        elapsed = time.time() - start
        
        stats = store.get_stats()
        throughput = 1000 / elapsed
        
        assert stats["total_tasks"] == 1000
        assert stats["memory_estimate_kb"] < 1024 * 100  # <100MB
        assert throughput >= 10  # At least 10 writes/sec
        
        print(f"\n100 Users scale: {stats['memory_estimate_kb']:.1f}KB, {throughput:.0f} writes/sec")
    
    def test_scale_matrix_10k_users(self):
        """10K users: <1GB memory, 1000+ writes/sec throughput."""
        store = CRDTTaskStore(replica_id="scale_10k")
        
        start = time.time()
        for i in range(10000):
            task = {
                "id": f"task_10k_{i:05d}",
                "title": f"10K-scale task {i}",
                "status": ["PENDING", "IN_PROGRESS", "COMPLETED"][i % 3],
                "tier": ["T1_PLANNING", "T2_CODE", "T3_REVIEW", "T4_DEPLOY"][i % 4],
                "created_at": int(time.time() * 1000),
                "assigned_to": f"agent_{i % 100}",
                "blocked_by": [f"task_10k_{(i-1):05d}"] if i > 0 else [],
            }
            store.add_task(task)
        elapsed = time.time() - start
        
        stats = store.get_stats()
        throughput = 10000 / elapsed
        
        assert stats["total_tasks"] == 10000
        assert stats["memory_estimate_kb"] < 1024 * 1024  # <1GB
        assert throughput >= 1000  # At least 1000 writes/sec
        
        print(f"\n10K Users scale: {stats['memory_estimate_kb']:.1f}KB, {throughput:.0f} writes/sec")


def run_tests():
    """Run all tests with formatted output."""
    print("\n" + "="*80)
    print("🧪 CRDT TASK STORE - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCRDTTaskStoreBasic))
    suite.addTests(loader.loadTestsFromTestCase(TestCRDTTaskStoreSerialize))
    suite.addTests(loader.loadTestsFromTestCase(TestCRDTTaskStoreMerge))
    suite.addTests(loader.loadTestsFromTestCase(TestCRDTTaskStoreStress))
    suite.addTests(loader.loadTestsFromTestCase(TestCRDTTaskStoreScaleMatrix))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")
    print("="*80 + "\n")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
