\"\"\"
Cluster Network - Distributed GPU Network
100 nodes working as one unified GPU supercomputer
\"\"\"

import time
import json
import hashlib
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class NetworkMessage:
    \"\"\"Message between cluster nodes.\"\"\"
    msg_id: str
    from_node: int
    to_node: int
    msg_type: str  # task, result, heartbeat, sync
    payload: Dict[str, Any]
    timestamp: str


class ClusterNetwork:
    \"\"\"
    Cluster Network - Distributed Communication Layer

    Features:
    - Message routing between nodes
    - Load balancing
    - Fault tolerance
    - Result aggregation
    \"\"\"

    def __init__(self, cluster):
        self.cluster = cluster
        self.message_log: List[NetworkMessage] = []
        self.routing_table: Dict[int, List[int]] = {}
        self._build_routing()

        print(f"Network layer initialized for {len(cluster.nodes)} nodes")

    def _build_routing(self) -> None:
        \"\"\"Build routing table for efficient communication.\"\"\"
        # Each node connects to 5 nearest neighbors
        for node in self.cluster.nodes:
            neighbors = [
                (node.node_id + i) % len(self.cluster.nodes)
                for i in range(1, 6)
            ]
            self.routing_table[node.node_id] = neighbors

    def broadcast(self, msg_type: str, payload: Dict[str, Any]) -> None:
        \"\"\"Broadcast message to all nodes.\"\"\"
        for node in self.cluster.nodes:
            msg = NetworkMessage(
                msg_id=self._generate_msg_id(),
                from_node=-1,  # Controller
                to_node=node.node_id,
                msg_type=msg_type,
                payload=payload,
                timestamp=datetime.utcnow().isoformat(),
            )
            self.message_log.append(msg)

    def send_to_node(self, node_id: int, msg_type: str, payload: Dict[str, Any]) -> None:
        \"\"\"Send message to specific node.\"\"\"
        msg = NetworkMessage(
            msg_id=self._generate_msg_id(),
            from_node=-1,
            to_node=node_id,
            msg_type=msg_type,
            payload=payload,
            timestamp=datetime.utcnow().isoformat(),
        )
        self.message_log.append(msg)

    def _generate_msg_id(self) -> str:
        \"\"\"Generate unique message ID.\"\"\"
        return hashlib.md5(
            f"{time.time()}-{random.randint(0, 1000000)}".encode()
        ).hexdigest()[:12]

    def get_node_load(self, node_id: int) -> float:
        \"\"\"Get current load of a node.\"\"\"
        node = self.cluster.get_node(node_id)
        if not node:
            return 1.0
        return 0.0 if node.status == "idle" else 1.0

    def find_best_node(self, required_vram: float = 0) -> Optional[int]:
        \"\"\"Find best available node based on load and VRAM.\"\"\"
        available = [
            n for n in self.cluster.nodes
            if n.status == "idle" and n.vram_gb >= required_vram
        ]

        if not available:
            return None

        # Sort by VRAM (largest first) then by task count (least first)
        available.sort(key=lambda n: (-n.vram_gb, n.total_tasks))
        return available[0].node_id

    def aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        \"\"\"Aggregate results from multiple nodes.\"\"\"
        successful = [r for r in results if r.get("status") == "success"]
        failed = [r for r in results if r.get("status") != "success"]

        return {
            "total_tasks": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(results) * 100 if results else 0,
            "results": successful,
            "errors": failed,
            "total_duration": sum(r.get("duration", 0) for r in results),
        }

    def print_network_stats(self) -> None:
        \"\"\"Print network statistics.\"\"\"
        table = Table(title="Cluster Network Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Messages", str(len(self.message_log)))
        table.add_row("Routing Table Size", str(len(self.routing_table)))
        table.add_row("Avg Neighbors/Node", "5")

        console.print(table)


import random
