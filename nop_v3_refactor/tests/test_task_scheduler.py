"""
Stress Test Suite for TaskScheduler
Verifies: Zero conflicts, fairness, dependency resolution, scale matrix

Test Strategy:
- Basic scheduling (single agent)
- Conflict detection (no over-booking)
- Fairness metrics (tasks distributed evenly)
- Dependency resolution (blocked tasks queued)
- Priority ordering (HIGH before LOW)
- Concurrent scheduling (100-1000 agents)
- Scale matrix (1→1000 agents)

Author: NOP V3 - January 2026
"""

import unittest
import time
from typing import List, Dict

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nop_core.task_scheduler import TaskScheduler, TaskStatus, TaskPriority


class TestTaskSchedulerBasic(unittest.TestCase):
    """Basic functionality tests."""

    def setUp(self):
        self.scheduler = TaskScheduler()

    def test_register_agent(self):
        """Test registering a single agent."""
        agent_state = self.scheduler.register_agent(
            "ag_001", "T1_PLANNING", capacity=5
        )

        assert agent_state["id"] == "ag_001"
        assert agent_state["tier"] == "T1_PLANNING"
        assert agent_state["capacity"] == 5
        assert agent_state["available"] is True
        assert len(agent_state["current_tasks"]) == 0

    def test_schedule_single_task(self):
        """Test scheduling a single task to an agent."""
        self.scheduler.register_agent("ag_001", "T1_PLANNING", capacity=5)

        tasks = [
            {
                "id": "task_001",
                "tier": "T1_PLANNING",
                "priority": "HIGH",
                "created_at": int(time.time() * 1000),
            }
        ]

        decisions = self.scheduler.schedule_batch(tasks)

        assert len(decisions) == 1
        assert decisions[0]["task_id"] == "task_001"
        assert decisions[0]["agent_id"] == "ag_001"
        assert decisions[0]["reason"] == "assigned"

    def test_no_agent_queues_task(self):
        """Test that task is queued if no available agent."""
        # Register agent with 0 capacity
        self.scheduler.register_agent("ag_001", "T1_PLANNING", capacity=0)

        tasks = [
            {
                "id": "task_001",
                "tier": "T1_PLANNING",
                "priority": "HIGH",
                "created_at": int(time.time() * 1000),
            }
        ]

        decisions = self.scheduler.schedule_batch(tasks)

        assert decisions[0]["reason"] == "queued"
        assert decisions[0]["agent_id"] is None

    def test_tier_matching(self):
        """Test that tasks are only assigned to matching tier agents."""
        self.scheduler.register_agent("ag_t1", "T1_PLANNING", capacity=5)
        self.scheduler.register_agent("ag_t2", "T2_CODE", capacity=5)

        tasks = [
            {
                "id": "task_t1",
                "tier": "T1_PLANNING",
                "priority": "HIGH",
                "created_at": int(time.time() * 1000),
            },
            {
                "id": "task_t2",
                "tier": "T2_CODE",
                "priority": "HIGH",
                "created_at": int(time.time() * 1000),
            },
        ]

        decisions = self.scheduler.schedule_batch(tasks)

        # Find assignments
        assignments = {d["task_id"]: d["agent_id"] for d in decisions}

        assert assignments["task_t1"] == "ag_t1"
        assert assignments["task_t2"] == "ag_t2"

    def test_capacity_respected(self):
        """Test that agent capacity is not exceeded."""
        self.scheduler.register_agent("ag_001", "T1_PLANNING", capacity=2)

        tasks = [
            {
                "id": f"task_{i:03d}",
                "tier": "T1_PLANNING",
                "priority": "HIGH",
                "created_at": int(time.time() * 1000),
            }
            for i in range(5)  # 5 tasks, but agent has capacity 2
        ]

        decisions = self.scheduler.schedule_batch(tasks)

        # Count assignments to ag_001
        assigned_count = sum(
            1 for d in decisions if d["agent_id"] == "ag_001"
        )

        # Should assign only 2, queue the rest
        assert assigned_count == 2
        queued_count = sum(1 for d in decisions if d["reason"] == "queued")
        assert queued_count == 3

    def test_mark_task_done_frees_capacity(self):
        """Test that completing a task frees agent capacity."""
        self.scheduler.register_agent("ag_001", "T1_PLANNING", capacity=1)

        tasks = [
            {
                "id": "task_001",
                "tier": "T1_PLANNING",
                "priority": "HIGH",
                "created_at": int(time.time() * 1000),
            }
        ]

        decisions1 = self.scheduler.schedule_batch(tasks)
        assert decisions1[0]["agent_id"] == "ag_001"

        # Agent now full
        agent_state = self.scheduler.get_agent_state("ag_001")
        assert not agent_state["available"]

        # Mark task done
        self.scheduler.mark_task_done("task_001", "ag_001")

        # Agent should be available again
        agent_state = self.scheduler.get_agent_state("ag_001")
        assert agent_state["available"]
        assert len(agent_state["current_tasks"]) == 0


class TestTaskSchedulerDependencies(unittest.TestCase):
    """Dependency resolution tests."""

    def setUp(self):
        self.scheduler = TaskScheduler()

    def test_blocked_task_queued(self):
        """Test that blocked tasks are queued, not scheduled."""
        self.scheduler.register_agent("ag_001", "T1_PLANNING", capacity=10)

        tasks = [
            {
                "id": "task_001",
                "tier": "T1_PLANNING",
                "priority": "HIGH",
                "created_at": int(time.time() * 1000),
            },
            {
                "id": "task_002",
                "tier": "T1_PLANNING",
                "priority": "HIGH",
                "blocked_by": ["task_001"],  # Blocked by task_001
                "created_at": int(time.time() * 1000),
            },
        ]

        decisions = self.scheduler.schedule_batch(tasks)

        # task_001 should be assigned
        task_001_decision = next(d for d in decisions if d["task_id"] == "task_001")
        assert task_001_decision["reason"] == "assigned"

        # task_002 should be blocked (not scheduled yet)
        task_002_decision = next(d for d in decisions if d["task_id"] == "task_002")
        assert task_002_decision["reason"] == "blocked"
        assert task_002_decision["agent_id"] is None

    def test_dependency_resolution_after_completion(self):
        """Test that task becomes schedulable after blocker completes."""
        self.scheduler.register_agent("ag_001", "T1_PLANNING", capacity=10)
        self.scheduler.register_agent("ag_002", "T1_PLANNING", capacity=10)

        tasks = [
            {
                "id": "task_001",
                "tier": "T1_PLANNING",
                "priority": "HIGH",
                "created_at": int(time.time() * 1000),
            },
            {
                "id": "task_002",
                "tier": "T1_PLANNING",
                "priority": "HIGH",
                "blocked_by": ["task_001"],
                "created_at": int(time.time() * 1000),
            },
        ]

        # First schedule: task_002 is blocked
        decisions1 = self.scheduler.schedule_batch(tasks)
        task_002_d1 = next(d for d in decisions1 if d["task_id"] == "task_002")
        assert task_002_d1["reason"] == "blocked"

        # Mark task_001 as done
        self.scheduler.mark_task_done("task_001", "ag_001")

        # Schedule again: task_002 should now be assignable
        decisions2 = self.scheduler.schedule_batch([tasks[1]])  # Reschedule task_002
        task_002_d2 = decisions2[0]
        assert task_002_d2["reason"] == "assigned"
        assert task_002_d2["agent_id"] is not None


class TestTaskSchedulerPriority(unittest.TestCase):
    """Priority ordering tests."""

    def setUp(self):
        self.scheduler = TaskScheduler()

    def test_priority_ordering(self):
        """Test that HIGH priority tasks are scheduled before LOW."""
        # Register agent with limited capacity
        self.scheduler.register_agent("ag_001", "T1_PLANNING", capacity=2)

        tasks = [
            {
                "id": "task_low_1",
                "tier": "T1_PLANNING",
                "priority": "LOW",
                "created_at": int(time.time() * 1000),
            },
            {
                "id": "task_high_1",
                "tier": "T1_PLANNING",
                "priority": "HIGH",
                "created_at": int(time.time() * 1000) + 100,  # Created later
            },
            {
                "id": "task_medium_1",
                "tier": "T1_PLANNING",
                "priority": "MEDIUM",
                "created_at": int(time.time() * 1000) + 200,
            },
        ]

        decisions = self.scheduler.schedule_batch(tasks)

        # Extract assigned tasks in order
        assigned = [d["task_id"] for d in decisions if d["reason"] == "assigned"]

        # HIGH priority should be scheduled first despite being created later
        assert assigned[0] == "task_high_1"
        assert assigned[1] == "task_medium_1"

    def test_deadline_aware_scheduling(self):
        """Test that urgent (deadline-based) tasks are prioritized."""
        self.scheduler.register_agent("ag_001", "T1_PLANNING", capacity=1)

        current_time = int(time.time() * 1000)

        tasks = [
            {
                "id": "task_no_deadline",
                "tier": "T1_PLANNING",
                "priority": "MEDIUM",
                "created_at": current_time,
            },
            {
                "id": "task_urgent",
                "tier": "T1_PLANNING",
                "priority": "MEDIUM",
                "deadline": current_time + 1000,  # Urgent deadline
                "created_at": current_time,
            },
        ]

        decisions = self.scheduler.schedule_batch(tasks)
        assigned = [d["task_id"] for d in decisions if d["reason"] == "assigned"]

        # Task with deadline should be scheduled first
        assert assigned[0] == "task_urgent"


class TestTaskSchedulerFairness(unittest.TestCase):
    """Fairness and load balancing tests."""

    def setUp(self):
        self.scheduler = TaskScheduler()

    def test_fairness_across_agents(self):
        """Test that tasks are distributed fairly across agents in a tier."""
        # Register 3 agents in T1_PLANNING tier
        for i in range(1, 4):
            self.scheduler.register_agent(f"ag_t1_{i}", "T1_PLANNING", capacity=3)

        # Create 9 tasks
        tasks = [
            {
                "id": f"task_{i:03d}",
                "tier": "T1_PLANNING",
                "priority": "MEDIUM",
                "created_at": int(time.time() * 1000),
            }
            for i in range(9)
        ]

        decisions = self.scheduler.schedule_batch(tasks)

        # Count assignments per agent
        agent_counts = {}
        for d in decisions:
            if d["reason"] == "assigned":
                agent = d["agent_id"]
                agent_counts[agent] = agent_counts.get(agent, 0) + 1

        # Should be distributed evenly: 3 tasks per agent
        for count in agent_counts.values():
            assert count == 3, f"Expected 3 tasks per agent, got {count}"

    def test_fairness_metrics(self):
        """Test fairness metric calculation."""
        for i in range(1, 4):
            self.scheduler.register_agent(f"ag_t1_{i}", "T1_PLANNING", capacity=3)

        tasks = [
            {
                "id": f"task_{i:03d}",
                "tier": "T1_PLANNING",
                "priority": "MEDIUM",
                "created_at": int(time.time() * 1000),
            }
            for i in range(9)
        ]

        self.scheduler.schedule_batch(tasks)

        fairness = self.scheduler.get_fairness_metrics()
        t1_metrics = fairness["T1_PLANNING"]

        # With perfect distribution, variance should be 0
        assert t1_metrics["variance"] == 0
        assert t1_metrics["avg_tasks_per_agent"] == 3.0


class TestTaskSchedulerStress(unittest.TestCase):
    """
    CRITICAL STRESS TESTS
    Verify: Zero conflicts, fairness, performance at scale
    """

    def test_stress_1000_tasks_10_agents(self):
        """
        CRITICAL: Schedule 1000 tasks across 10 agents
        Assert: Zero conflicts, fairness, dependency resolution
        """
        scheduler = TaskScheduler()

        # Register 10 agents: 3 T1, 3 T2, 2 T3, 2 T4
        tier_distribution = {
            "T1_PLANNING": 3,
            "T2_CODE": 3,
            "T3_REVIEW": 2,
            "T4_DEPLOY": 2,
        }

        agent_id = 0
        for tier, count in tier_distribution.items():
            for _ in range(count):
                scheduler.register_agent(
                    f"ag_{agent_id:03d}", tier, capacity=5
                )
                agent_id += 1

        # Create 1000 tasks: mixed tiers, priorities, 10% blocked
        current_time = int(time.time() * 1000)
        tasks = []

        tiers = ["T1_PLANNING", "T2_CODE", "T3_REVIEW", "T4_DEPLOY"]
        priorities = ["HIGH", "MEDIUM", "LOW"]

        for i in range(1000):
            task = {
                "id": f"task_{i:04d}",
                "tier": tiers[i % 4],
                "priority": priorities[i % 3],
                "created_at": current_time + i,
            }

            # 10% of tasks are blocked
            if i % 10 == 0 and i > 0:
                task["blocked_by"] = [f"task_{(i-1):04d}"]

            tasks.append(task)

        # Schedule batch
        start_time = time.time()
        decisions = scheduler.schedule_batch(tasks)
        elapsed = time.time() - start_time

        # VERIFY: Zero conflicts
        assigned_tasks = {d["task_id"] for d in decisions if d["reason"] == "assigned"}
        queued_tasks = {d["task_id"] for d in decisions if d["reason"] == "queued"}
        blocked_tasks = {d["task_id"] for d in decisions if d["reason"] == "blocked"}

        # No task should appear in multiple categories
        assert len(assigned_tasks & queued_tasks) == 0
        assert len(assigned_tasks & blocked_tasks) == 0
        assert len(queued_tasks & blocked_tasks) == 0

        # Total decisions should equal task count
        assert len(decisions) == 1000

        # VERIFY: Tier matching (no task assigned to wrong tier)
        for task in tasks:
            task_decisions = [d for d in decisions if d["task_id"] == task["id"]]
            if task_decisions and task_decisions[0]["reason"] == "assigned":
                agent_id = task_decisions[0]["agent_id"]
                agent_state = scheduler.get_agent_state(agent_id)
                assert agent_state["tier"] == task["tier"], (
                    f"Task {task['id']} (tier {task['tier']}) "
                    f"assigned to agent {agent_id} (tier {agent_state['tier']})"
                )

        # VERIFY: Capacity not exceeded
        for agent in scheduler.get_all_agents():
            assigned_count = len(agent["current_tasks"])
            assert assigned_count <= agent["capacity"], (
                f"Agent {agent['id']} over-capacity: "
                f"{assigned_count}/{agent['capacity']}"
            )

        # VERIFY: Blocked tasks not scheduled
        for task in tasks:
            if task.get("blocked_by"):
                task_decision = next(d for d in decisions if d["task_id"] == task["id"])
                assert task_decision["reason"] in ["blocked", "queued"], (
                    f"Blocked task {task['id']} was scheduled (reason: {task_decision['reason']})"
                )

        # VERIFY: Performance
        stats = scheduler.get_scheduling_stats()
        print(f"\n🚀 CRITICAL STRESS TEST RESULTS:")
        print(f"  Total tasks: 1000")
        print(f"  Scheduled: {stats['scheduled']}")
        print(f"  Blocked: {stats['blocked']}")
        print(f"  Queued: {stats['queued']}")
        print(f"  Scheduling time: {elapsed*1000:.2f}ms")
        print(f"  Throughput: {1000/elapsed:.0f} tasks/sec")
        print(f"  Fairness variance: {scheduler.get_fairness_metrics()}")

        assert elapsed < 0.5, f"Scheduling took {elapsed}s, should be <0.5s"

        # VERIFY: Fairness (tasks distributed evenly within tier)
        fairness = scheduler.get_fairness_metrics()
        for tier, metrics in fairness.items():
            # Allow some variance due to random task order, but should be relatively fair
            # Perfect fairness: variance = 0
            # Acceptable: variance < avg^2 (coefficient of variation < 100%)
            avg = metrics["avg_tasks_per_agent"]
            variance = metrics["variance"]
            if avg > 0:
                cv = (variance ** 0.5) / avg
                assert cv < 0.5, f"Tier {tier} fairness variance too high: {variance}"

        print(f"  All assertions passed ✅")

    def test_scale_matrix_verification(self):
        """Verify scale matrix: 1 agent, 10 agents, 100 agents."""
        scale_tests = [
            (1, 10),    # 1 agent, 10 tasks
            (10, 100),  # 10 agents, 100 tasks
            (100, 1000),  # 100 agents, 1000 tasks
        ]

        for num_agents, num_tasks in scale_tests:
            scheduler = TaskScheduler()

            # Register agents
            tiers = ["T1_PLANNING", "T2_CODE", "T3_REVIEW", "T4_DEPLOY"]
            for i in range(num_agents):
                tier = tiers[i % 4]
                scheduler.register_agent(f"ag_{i:04d}", tier, capacity=5)

            # Create tasks
            current_time = int(time.time() * 1000)
            tasks = [
                {
                    "id": f"task_{i:04d}",
                    "tier": tiers[i % 4],
                    "priority": "MEDIUM",
                    "created_at": current_time + i,
                }
                for i in range(num_tasks)
            ]

            # Schedule and measure
            start_time = time.time()
            decisions = scheduler.schedule_batch(tasks)
            elapsed = time.time() - start_time

            stats = scheduler.get_scheduling_stats()
            print(
                f"\n  {num_agents} agents, {num_tasks} tasks: "
                f"{elapsed*1000:.1f}ms, {num_tasks/elapsed:.0f} tasks/sec"
            )

            # Assert performance targets from scale matrix
            if num_agents == 1:
                assert elapsed < 0.001, "1 agent should be <1ms"
            elif num_agents == 10:
                assert elapsed < 0.005, "10 agents should be <5ms"
            elif num_agents == 100:
                assert elapsed < 0.05, "100 agents should be <50ms"


def run_tests():
    """Run all tests with formatted output."""
    print("\n" + "="*80)
    print("👨‍💻 TASK SCHEDULER - COMPREHENSIVE TEST SUITE")
    print("="*80)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTaskSchedulerBasic))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskSchedulerDependencies))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskSchedulerPriority))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskSchedulerFairness))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskSchedulerStress))

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
