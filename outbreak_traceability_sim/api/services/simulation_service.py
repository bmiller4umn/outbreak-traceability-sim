"""
Simulation service for managing simulation runs.

Handles async simulation execution and result storage.
"""

import asyncio
import uuid
import threading
from uuid import UUID
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from ...simulation.runner import OutbreakSimulator, SimulationConfig
from ...simulation.timing import TimingConfig
from ...models.nodes import LotCodeAssignmentMode, CalculatedLotCodeMethod


class SimulationStatus(str, Enum):
    """Simulation execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class SimulationRun:
    """Tracks a single simulation run."""
    id: str
    config: dict
    status: SimulationStatus = SimulationStatus.PENDING
    progress: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[dict] = None
    error: Optional[str] = None

    # Internal simulation components
    simulator: Optional[OutbreakSimulator] = None
    network_data: Optional[dict] = None
    investigation_data: Optional[dict] = None


class SimulationService:
    """
    Service for managing simulation runs.

    Maintains an in-memory store of simulation runs and their results.
    In production, this would be backed by a database.
    """

    # Maximum number of simulations to keep in memory
    MAX_STORED_SIMULATIONS = 50

    def __init__(self):
        self.runs: Dict[str, SimulationRun] = {}
        self._lock = threading.Lock()

    def _cleanup_old_simulations(self) -> None:
        """Remove oldest completed simulations if we've exceeded the limit."""
        with self._lock:
            if len(self.runs) < self.MAX_STORED_SIMULATIONS:
                return

            # Get completed simulations sorted by completion time (oldest first)
            completed_runs = [
                (run_id, run) for run_id, run in self.runs.items()
                if run.status in (SimulationStatus.COMPLETED, SimulationStatus.ERROR)
                and run.completed_at is not None
            ]
            completed_runs.sort(key=lambda x: x[1].completed_at or datetime.min)

            # Remove oldest simulations to get below limit
            num_to_remove = len(self.runs) - self.MAX_STORED_SIMULATIONS + 10  # Remove 10 extra for headroom
            for run_id, run in completed_runs[:num_to_remove]:
                # Release simulator memory and clear large objects before removing
                self._release_simulator_memory(run)
                run.network_data = None
                run.investigation_data = None
                del self.runs[run_id]

    def _release_simulator_memory(self, run: SimulationRun) -> None:
        """
        Release memory from simulator by clearing large internal structures.

        WARNING: Do not call this immediately after simulation completion!
        Investigation endpoints (get_farm_traceback_metrics, get_investigation_scope)
        require flow_sim.node_inventory and flow_sim.shipments to function.

        This method is intended for use by _cleanup_old_simulations when removing
        simulations that are no longer needed, to help garbage collection.
        """
        if run.simulator:
            if hasattr(run.simulator, 'flow_sim') and run.simulator.flow_sim:
                run.simulator.flow_sim.shipments = []
                run.simulator.flow_sim.production_batches = []
                run.simulator.flow_sim.node_inventory = {}
            run.simulator = None

    def create_simulation(self, config: dict) -> str:
        """Create a new simulation run and return its ID."""
        # Clean up old simulations to prevent memory growth
        self._cleanup_old_simulations()

        simulation_id = str(uuid.uuid4())

        run = SimulationRun(
            id=simulation_id,
            config=config,
            status=SimulationStatus.PENDING,
        )
        with self._lock:
            self.runs[simulation_id] = run

        return simulation_id

    def get_run(self, simulation_id: str) -> Optional[SimulationRun]:
        """Get a simulation run by ID."""
        with self._lock:
            return self.runs.get(simulation_id)

    def _run_simulation_sync(self, simulation_id: str) -> None:
        """Execute a simulation synchronously (called from thread pool)."""
        with self._lock:
            run = self.runs.get(simulation_id)
        if not run:
            return

        try:
            # Build simulation config
            config = run.config

            # Map inventory strategy to lot code assignment mode
            strategy = config.get("inventory_strategy", "FIFO")
            if strategy in ("FIFO", "LIFO", "ALL_IN_WINDOW", "INVENTORY_WEIGHTED"):
                dc_mode = LotCodeAssignmentMode.CALCULATED
                method_map = {
                    "FIFO": CalculatedLotCodeMethod.FIFO_DATE_RANGE,
                    "LIFO": CalculatedLotCodeMethod.LIFO_DATE_RANGE,
                    "ALL_IN_WINDOW": CalculatedLotCodeMethod.ALL_IN_WINDOW,
                    "INVENTORY_WEIGHTED": CalculatedLotCodeMethod.INVENTORY_WEIGHTED,
                }
                dc_method = method_map.get(strategy, CalculatedLotCodeMethod.FIFO_DATE_RANGE)
            else:
                dc_mode = LotCodeAssignmentMode.DETERMINISTIC
                dc_method = None

            # Build timing configuration from request parameters
            timing_config = TimingConfig(
                speed_factor=config.get("transit_speed_factor", 1.0),
                cooling_hold_hours=config.get("cooling_hold_hours", 12.0),
                dc_receiving_inspection_hours=config.get("dc_inspection_hours", 6.0),
                retail_stocking_delay_hours=config.get("retail_stocking_delay_hours", 4.0),
            )

            sim_config = SimulationConfig(
                start_date=date.today() - timedelta(days=config.get("simulation_days", 90)),
                end_date=date.today(),
                num_farms=config.get("num_farms", 5),
                num_packers=config.get("num_packers", 2),
                num_distribution_centers=config.get("num_distribution_centers", 3),
                num_retailers=config.get("num_retailers", 20),
                retailers_with_delis_pct=config.get("retailers_with_delis_pct", 0.3),
                contamination_rate=config.get("contamination_rate", 1.0),
                contamination_duration_days=config.get("contamination_duration_days", 7),
                pathogen=config.get("pathogen", "Salmonella"),
                random_seed=config.get("random_seed"),
                # Investigation parameters
                interview_success_rate=config.get("interview_success_rate", 0.7),
                record_collection_window_days=config.get("record_collection_window_days", 14),
                num_investigators=config.get("num_investigators", 5),
                # Timing configuration
                timing_config=timing_config,
            )

            run.progress = 0.2

            # Run simulation
            simulator = OutbreakSimulator(sim_config)
            run.simulator = simulator

            run.progress = 0.3

            # Run the comparison
            result = simulator.run_comparison()

            run.progress = 0.8

            # Extract network data for visualization
            network_data = self._extract_network_data(simulator)
            run.network_data = network_data

            # Extract investigation data
            investigation_data = self._extract_investigation_data(simulator)
            run.investigation_data = investigation_data

            run.progress = 1.0
            run.result = result
            run.status = SimulationStatus.COMPLETED
            run.completed_at = datetime.now()

            # Note: We don't release simulator memory here because investigation
            # endpoints (get_farm_traceback_metrics, get_investigation_scope) need
            # flow_sim.node_inventory and flow_sim.shipments. Memory is managed
            # by _cleanup_old_simulations which removes entire old runs.

        except Exception as e:
            run.status = SimulationStatus.ERROR
            run.error = str(e)
            run.completed_at = datetime.now()

    async def run_simulation(self, simulation_id: str) -> None:
        """Execute a simulation asynchronously."""
        run = self.runs.get(simulation_id)
        if not run:
            return

        run.status = SimulationStatus.RUNNING
        run.started_at = datetime.now()
        run.progress = 0.1

        # Run the blocking simulation work in a thread pool
        # to avoid blocking the asyncio event loop
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._run_simulation_sync, simulation_id)

    def _extract_network_data(self, simulator: OutbreakSimulator) -> dict:
        """Extract network graph data for visualization."""
        if not simulator.network:
            return {"nodes": [], "edges": []}

        network = simulator.network
        seeder = simulator.seeder
        lot_graph = simulator.lot_graph
        flow_sim = simulator.flow_sim

        # Build a map of node_id -> max contamination probability
        node_contamination: Dict[str, float] = {}
        contamination_sources: set[str] = set()

        # Get all contaminated TLCs for easy lookup
        contaminated_tlcs: Dict[str, float] = {}
        if seeder:
            # Mark contamination source farms
            for event in seeder.contamination_events:
                contamination_sources.add(str(event.farm_id))

            # Build contaminated TLC lookup
            for tlc in seeder.contaminated_source_tlcs:
                contaminated_tlcs[tlc] = 1.0
            for tlc, prob in seeder.contamination_propagation.items():
                if tlc not in contaminated_tlcs:
                    contaminated_tlcs[tlc] = prob
                else:
                    contaminated_tlcs[tlc] = max(contaminated_tlcs[tlc], prob)

        # Method 1: Track nodes that CREATED contaminated TLCs
        if lot_graph and seeder:
            for tlc, lot_record in lot_graph.lots.items():
                prob = contaminated_tlcs.get(tlc, 0.0)
                if prob == 0 and lot_record.is_contaminated:
                    prob = lot_record.contamination_probability

                if prob > 0:
                    node_id_str = str(lot_record.created_by_node_id)
                    if node_id_str not in node_contamination:
                        node_contamination[node_id_str] = prob
                    else:
                        node_contamination[node_id_str] = max(
                            node_contamination[node_id_str], prob
                        )

        # Method 2: Track nodes that RECEIVED contaminated shipments
        # This catches retailers and other endpoints that don't create TLCs
        if flow_sim and seeder:
            for shipment in flow_sim.shipments:
                # Check if any TLC in this shipment is contaminated
                max_prob = 0.0
                for tlc in shipment.source_tlcs:
                    if tlc in contaminated_tlcs:
                        max_prob = max(max_prob, contaminated_tlcs[tlc])

                # Also check the shipment's own contamination tracking
                if shipment.contains_contaminated_product:
                    max_prob = max(max_prob, shipment.contamination_probability or 1.0)

                if max_prob > 0:
                    dest_id_str = str(shipment.dest_node_id)
                    if dest_id_str not in node_contamination:
                        node_contamination[dest_id_str] = max_prob
                    else:
                        node_contamination[dest_id_str] = max(
                            node_contamination[dest_id_str], max_prob
                        )

        nodes = []
        for node_id, node in network.nodes.items():
            # Get node name and type
            node_type = node.node_type.value

            if hasattr(node, 'farm_name'):
                name = node.farm_name
            elif hasattr(node, 'facility_name'):
                name = node.facility_name
            elif hasattr(node, 'store_name'):
                name = f"{node.store_name} #{node.store_number}"
            else:
                name = str(node_id)[:8]

            node_id_str = str(node_id)

            # Check if this node is a contamination source
            is_source = node_id_str in contamination_sources

            # Check if this node received contaminated product
            contamination_prob = node_contamination.get(node_id_str, 0.0)
            received_contaminated = contamination_prob > 0

            # A node is "contaminated" if it's either the source or received contaminated product
            is_contaminated = is_source or received_contaminated

            nodes.append({
                "id": node_id_str,
                "type": node_type,
                "name": name,
                "city": node.location.city,
                "state": node.location.state,
                "is_contaminated": is_contaminated,
                "is_contamination_source": is_source,
                "contamination_probability": contamination_prob if not is_source else 1.0,
            })

        edges = []
        for i, edge in enumerate(network.edges):
            edges.append({
                "id": f"edge-{i}",
                "source": str(edge.source_id),
                "target": str(edge.destination_id),
                "product_categories": [pc.value for pc in edge.product_categories],
                "shipment_volume": edge.typical_volume_per_shipment.value,
            })

        return {"nodes": nodes, "edges": edges}

    def _extract_investigation_data(self, simulator: OutbreakSimulator) -> dict:
        """Extract investigation data for animation."""
        # Generate traceback steps for animation
        # This is a simplified version - in production would be more detailed

        deterministic_steps = []
        probabilistic_steps = []

        if simulator.cases and simulator.lot_graph:
            # Get interviewed cases for animation (realistic investigation model)
            interviewed_cases = [
                c for c in simulator.cases
                if c.was_interviewed and c.reported_exposure_location_id
            ]
            sample_cases = interviewed_cases[:5] if len(interviewed_cases) > 5 else interviewed_cases

            for i, case in enumerate(sample_cases):
                # Use actual contamination source TLC for visualization (ground truth)
                tlc = case.actual_contamination_source_tlc or f"TLC-{i}"
                location_id = str(case.reported_exposure_location_id or case.exposure_location_id)

                # Deterministic step
                deterministic_steps.append({
                    "step_index": i,
                    "current_node_id": location_id,
                    "current_tlc": tlc,
                    "probability": 1.0,
                    "mode": "deterministic",
                    "path_so_far": [location_id],
                    "branching_factor": 1,
                })

                # Probabilistic step (simulated uncertainty)
                probabilistic_steps.append({
                    "step_index": i,
                    "current_node_id": location_id,
                    "current_tlc": tlc,
                    "probability": max(0.1, 1.0 - (i * 0.15)),
                    "mode": "probabilistic",
                    "path_so_far": [location_id],
                    "branching_factor": min(i + 1, 5),
                })

        actual_source = None
        if simulator.contaminated_farm_id:
            actual_source = str(simulator.contaminated_farm_id)

        return {
            "deterministic_steps": deterministic_steps,
            "probabilistic_steps": probabilistic_steps,
            "actual_source_farm_id": actual_source,
        }

    def get_convergence_results(self, simulation_id: str) -> list:
        """Get convergence analysis results (legacy - use get_farm_traceback_metrics instead)."""
        metrics = self.get_farm_traceback_metrics(simulation_id)
        # Return probabilistic results for backward compatibility
        return metrics.get("probabilistic", {}).get("farms", [])

    def get_farm_traceback_metrics(self, simulation_id: str) -> dict:
        """
        Get per-farm traceback metrics for both deterministic and probabilistic modes.

        Returns convergence analysis showing which farms the cases trace back to,
        with metrics like case coverage, exclusive cases, and confidence scores.
        """
        run = self.runs.get(simulation_id)
        if not run or not run.result or not run.simulator:
            return {"deterministic": {"farms": []}, "probabilistic": {"farms": []}}

        simulator = run.simulator
        network = simulator.network
        flow_sim = simulator.flow_sim
        cases = simulator.cases

        if not network or not flow_sim or not cases:
            return {"deterministic": {"farms": []}, "probabilistic": {"farms": []}}

        # Import here to avoid circular imports
        from ...simulation.investigation import InvestigationEngine

        # Get config for record window
        config = run.config or {}
        record_window = config.get("record_collection_window_days", 14)

        # Get actual source farm for ground truth
        actual_source_id = simulator.contaminated_farm_id
        actual_source_name = ""
        if actual_source_id and actual_source_id in network.farms:
            actual_source_name = network.farms[actual_source_id].farm_name

        def assign_tier(rank: int, score: float, top_score: float, exclusive_cases: int, has_clear_leader: bool) -> str:
            """
            Assign investigation tier based on evidence strength.

            Tiers:
            - "Primary Suspect": Strong evidence this is the source
            - "Cannot Rule Out": Insufficient evidence to exclude
            - "Unlikely": Weak evidence, probably not the source
            """
            CONFIDENCE_GAP_THRESHOLD = 0.10  # Minimum gap to distinguish farms

            if rank == 1:
                # Top ranked farm
                if has_clear_leader or exclusive_cases > 0:
                    return "Primary Suspect"
                else:
                    # Top ranked but no clear separation
                    return "Cannot Rule Out"
            elif (top_score - score) <= CONFIDENCE_GAP_THRESHOLD:
                # Within threshold of top score - statistically indistinguishable
                return "Cannot Rule Out"
            elif score >= 0.20 or exclusive_cases > 0:
                # Some meaningful evidence
                return "Cannot Rule Out"
            else:
                return "Unlikely"

        def extract_farm_metrics(engine: InvestigationEngine, cases: list) -> dict:
            """Extract farm metrics from convergence analysis."""
            convergence_results = engine.analyze_convergence(cases)

            if not convergence_results:
                return {
                    "farms": [],
                    "total_cases": len(cases),
                    "cases_with_traces": 0,
                }

            # Get top score and determine if there's a clear leader
            top_score = convergence_results[0].confidence_score
            second_score = convergence_results[1].confidence_score if len(convergence_results) > 1 else 0
            has_clear_leader = (top_score - second_score) > 0.10

            farms = []
            for rank, cr in enumerate(convergence_results, 1):
                is_actual_source = str(cr.farm_id) == str(actual_source_id) if actual_source_id else False
                tier = assign_tier(rank, cr.confidence_score, top_score, cr.exclusive_cases, has_clear_leader)

                farms.append({
                    "farm_id": str(cr.farm_id),
                    "farm_name": cr.farm_name,
                    "rank": rank,
                    "tier": tier,
                    "cases_converging": cr.cases_converging,
                    "exclusive_cases": cr.exclusive_cases,
                    "total_cases_analyzed": cr.total_cases_analyzed,
                    "case_coverage_pct": round(cr.case_coverage_pct, 1),
                    "exclusive_case_pct": round(cr.exclusive_case_pct, 1),
                    "tlcs_converging": len(cr.tlcs_converging),
                    "retail_locations": len(cr.retail_locations_converging),
                    "convergence_probability": round(cr.convergence_probability, 3),
                    "confidence_score": round(cr.confidence_score, 3),
                    "is_actual_source": is_actual_source,
                })

            return {
                "farms": farms,
                "total_cases": len(cases),
                "cases_with_traces": convergence_results[0].total_cases_analyzed if convergence_results else 0,
                "has_clear_leader": has_clear_leader,
            }

        # Run deterministic investigation
        det_engine = InvestigationEngine(
            network,
            flow_sim.lot_graph,
            is_probabilistic=False,
            record_collection_window_days=record_window,
            node_inventory=flow_sim.node_inventory,
            tlc_shipment_map=flow_sim.tlc_shipment_map
        )
        det_metrics = extract_farm_metrics(det_engine, cases)
        det_metrics["mode"] = "deterministic"

        # Run probabilistic investigation
        prob_engine = InvestigationEngine(
            network,
            flow_sim.lot_graph,
            is_probabilistic=True,
            record_collection_window_days=record_window,
            node_inventory=flow_sim.node_inventory,
            tlc_shipment_map=flow_sim.tlc_shipment_map
        )
        prob_metrics = extract_farm_metrics(prob_engine, cases)
        prob_metrics["mode"] = "probabilistic"

        return {
            "deterministic": det_metrics,
            "probabilistic": prob_metrics,
            "actual_source": {
                "farm_id": str(actual_source_id) if actual_source_id else None,
                "farm_name": actual_source_name,
            }
        }

    def get_investigation_scope(self, simulation_id: str) -> dict:
        """
        Get downstream contamination scope for deterministic vs probabilistic modes.

        Shows which retail endpoints (delis, retailers) could have received
        contaminated product. The key difference:
        - Deterministic: We know EXACTLY which endpoints received contaminated product
        - Probabilistic: We must consider ALL endpoints that COULD have received it
          (wider net due to uncertainty at DC level)

        For each endpoint node, we calculate the TLC Scope Expansion - the ratio of
        TLCs that need to be traced in probabilistic vs deterministic mode.
        """
        run = self.runs.get(simulation_id)
        if not run or not run.result or not run.simulator:
            return {"deterministic": {}, "probabilistic": {}}

        simulator = run.simulator
        network = simulator.network
        flow_sim = simulator.flow_sim
        seeder = simulator.seeder

        if not network or not flow_sim or not seeder:
            return {"deterministic": {}, "probabilistic": {}}

        # Get contaminated TLCs from seeder
        contaminated_tlcs: set[str] = set(seeder.contaminated_source_tlcs)
        for tlc in seeder.contamination_propagation.keys():
            contaminated_tlcs.add(tlc)

        # Track nodes and edges for each mode
        det_nodes: Dict[str, dict] = {}
        det_edges: Dict[str, dict] = {}
        prob_nodes: Dict[str, dict] = {}
        prob_edges: Dict[str, dict] = {}

        # Track TLCs per node for calculating expansion factor
        # These track contaminated TLCs that need to be traced at each node
        det_tlcs_by_node: Dict[str, set] = {}  # node_id -> set of TLCs (deterministic)
        prob_tlcs_by_node: Dict[str, set] = {}  # node_id -> set of TLCs (probabilistic)

        # Helper to get node name
        def get_node_name(node_obj) -> str:
            if hasattr(node_obj, 'farm_name'):
                return node_obj.farm_name
            elif hasattr(node_obj, 'facility_name'):
                return node_obj.facility_name
            elif hasattr(node_obj, 'store_name'):
                return f"{node_obj.store_name} #{node_obj.store_number}"
            else:
                return str(node_obj.id)[:8]

        # Helper to add a node (without probability - we'll add expansion later)
        def add_node(nodes_dict: Dict[str, dict], node_id: UUID):
            node_id_str = str(node_id)
            if node_id_str in nodes_dict:
                return
            node_obj = network.get_node(node_id)
            if not node_obj:
                return
            nodes_dict[node_id_str] = {
                "id": node_id_str,
                "name": get_node_name(node_obj),
                "type": node_obj.node_type.value,
                "city": node_obj.location.city if node_obj.location else "",
                "state": node_obj.location.state if node_obj.location else "",
                "probability": 1.0,  # Will be replaced with expansion factor for endpoints
            }

        # Helper to add an edge
        def add_edge(edges_dict: Dict[str, dict], source_id: UUID, target_id: UUID, probability: float = 1.0):
            edge_key = f"{source_id}->{target_id}"
            if edge_key in edges_dict:
                edges_dict[edge_key]["probability"] = max(
                    edges_dict[edge_key]["probability"], probability
                )
                return
            edges_dict[edge_key] = {
                "id": edge_key,
                "source": str(source_id),
                "target": str(target_id),
                "probability": probability,
            }

        # Helper to add TLCs to a node's tracking set
        def add_tlcs_to_node(tlcs_dict: Dict[str, set], node_id: UUID, tlcs: set):
            node_id_str = str(node_id)
            if node_id_str not in tlcs_dict:
                tlcs_dict[node_id_str] = set()
            tlcs_dict[node_id_str].update(tlcs)

        # Add contaminated source farm to both
        if simulator.contaminated_farm_id:
            add_node(det_nodes, simulator.contaminated_farm_id)
            add_node(prob_nodes, simulator.contaminated_farm_id)

        # Track which DCs received contaminated product (for probabilistic expansion)
        contaminated_dcs: set[UUID] = set()

        # Process all shipments to trace contamination flow
        for shipment in flow_sim.shipments:
            source_id = shipment.source_node_id
            dest_id = shipment.dest_node_id

            # Find contaminated TLCs in this shipment (deterministic - ground truth)
            shipment_contaminated_tlcs = set(tlc for tlc in shipment.source_tlcs if tlc in contaminated_tlcs)
            has_contaminated_tlc = len(shipment_contaminated_tlcs) > 0

            if has_contaminated_tlc or shipment.contains_contaminated_product:
                # DETERMINISTIC: Add nodes/edges only for confirmed contaminated shipments
                add_node(det_nodes, source_id)
                add_node(det_nodes, dest_id)
                add_edge(det_edges, source_id, dest_id, 1.0)

                # Track which contaminated TLCs this destination received
                add_tlcs_to_node(det_tlcs_by_node, dest_id, shipment_contaminated_tlcs)

                # Track if destination is a DC (for probabilistic expansion)
                dest_node = network.get_node(dest_id)
                if dest_node and dest_node.node_type.value == "distribution_center":
                    contaminated_dcs.add(dest_id)

            # PROBABILISTIC: Track TLCs from probabilistic linkages
            if shipment.tlc_probabilities:
                # Find all TLCs in the probability distribution that are contaminated
                prob_contaminated_tlcs = set(
                    tlc for tlc, prob in shipment.tlc_probabilities.items()
                    if tlc in contaminated_tlcs and prob > 0
                )
                if prob_contaminated_tlcs:
                    add_node(prob_nodes, source_id)
                    add_node(prob_nodes, dest_id)
                    add_edge(prob_edges, source_id, dest_id, 1.0)

                    # Track all probabilistic TLCs (contaminated ones) for this destination
                    add_tlcs_to_node(prob_tlcs_by_node, dest_id, prob_contaminated_tlcs)

                    dest_node = network.get_node(dest_id)
                    if dest_node and dest_node.node_type.value == "distribution_center":
                        contaminated_dcs.add(dest_id)

        # PROBABILISTIC EXPANSION: For each contaminated DC, add ALL its outbound destinations
        # and track all TLCs that COULD have been in each shipment
        for shipment in flow_sim.shipments:
            source_id = shipment.source_node_id
            if source_id in contaminated_dcs:
                dest_id = shipment.dest_node_id
                add_node(prob_nodes, source_id)
                add_node(prob_nodes, dest_id)
                add_edge(prob_edges, source_id, dest_id, 1.0)

                # For probabilistic, add ALL TLCs from the probability distribution
                # (these are all TLCs that COULD have been in this shipment)
                if shipment.tlc_probabilities:
                    # Add all TLCs in the probability distribution that are contaminated
                    all_prob_tlcs = set(
                        tlc for tlc, prob in shipment.tlc_probabilities.items()
                        if tlc in contaminated_tlcs and prob > 0
                    )
                    add_tlcs_to_node(prob_tlcs_by_node, dest_id, all_prob_tlcs)

        # Also include deterministic nodes/TLCs in probabilistic (it's a superset)
        for node_id, node_data in det_nodes.items():
            if node_id not in prob_nodes:
                prob_nodes[node_id] = node_data.copy()
        for edge_id, edge_data in det_edges.items():
            if edge_id not in prob_edges:
                prob_edges[edge_id] = edge_data.copy()
        for node_id, tlcs in det_tlcs_by_node.items():
            if node_id not in prob_tlcs_by_node:
                prob_tlcs_by_node[node_id] = set()
            prob_tlcs_by_node[node_id].update(tlcs)

        # Calculate TLC expansion factor for each endpoint and update node probability field
        for node_id, node_data in prob_nodes.items():
            if node_data["type"] in ["deli", "retailer"]:
                det_tlc_count = len(det_tlcs_by_node.get(node_id, set()))
                prob_tlc_count = len(prob_tlcs_by_node.get(node_id, set()))

                if det_tlc_count > 0:
                    # Expansion factor: how many more TLCs to trace in probabilistic vs deterministic
                    expansion = prob_tlc_count / det_tlc_count
                elif prob_tlc_count > 0:
                    # Node only appears in probabilistic mode - use prob count as expansion
                    # (this means deterministic would have 0, so infinite expansion - cap it)
                    expansion = float(prob_tlc_count)  # Show absolute count as "expansion"
                else:
                    expansion = 1.0

                # Store expansion factor in the probability field (repurposed)
                # Also store the actual TLC counts for tooltips
                node_data["probability"] = expansion
                node_data["detTlcCount"] = det_tlc_count
                node_data["probTlcCount"] = prob_tlc_count

        # Count endpoints (delis + retailers) for each mode
        det_endpoints = sum(1 for n in det_nodes.values() if n["type"] in ["deli", "retailer"])
        prob_endpoints = sum(1 for n in prob_nodes.values() if n["type"] in ["deli", "retailer"])

        return {
            "deterministic": {
                "nodes": list(det_nodes.values()),
                "edges": list(det_edges.values()),
                "farmsCount": sum(1 for n in det_nodes.values() if n["type"] == "farm"),
                "tlcsCount": len(contaminated_tlcs),
                "pathsCount": det_endpoints,  # Use endpoint count as "paths"
            },
            "probabilistic": {
                "nodes": list(prob_nodes.values()),
                "edges": list(prob_edges.values()),
                "farmsCount": sum(1 for n in prob_nodes.values() if n["type"] == "farm"),
                "tlcsCount": len(contaminated_tlcs),
                "pathsCount": prob_endpoints,  # Use endpoint count as "paths"
            },
            "actual_source_farm_id": str(simulator.contaminated_farm_id) if simulator.contaminated_farm_id else None,
        }


    def get_case_data(self, simulation_id: str) -> dict:
        """
        Get case data for visualizations including epi curve, summary, and per-node counts.
        """
        run = self.runs.get(simulation_id)
        if not run or not run.simulator:
            return {
                "epi_curve": [],
                "summary": {
                    "total_cases": 0,
                    "hospitalized_cases": 0,
                    "hospitalization_rate": 0.0,
                    "interviewed_cases": 0,
                    "interview_rate": 0.0,
                    "cases_with_exposure_location": 0,
                    "exposure_location_rate": 0.0,
                    "earliest_onset": None,
                    "latest_onset": None,
                    "outbreak_duration_days": 0,
                },
                "node_case_counts": [],
            }

        simulator = run.simulator
        cases = simulator.cases or []
        network = simulator.network

        if not cases:
            return {
                "epi_curve": [],
                "summary": {
                    "total_cases": 0,
                    "hospitalized_cases": 0,
                    "hospitalization_rate": 0.0,
                    "interviewed_cases": 0,
                    "interview_rate": 0.0,
                    "cases_with_exposure_location": 0,
                    "exposure_location_rate": 0.0,
                    "earliest_onset": None,
                    "latest_onset": None,
                    "outbreak_duration_days": 0,
                },
                "node_case_counts": [],
            }

        # Build epi curve data (cases by onset date)
        onset_counts: Dict[str, int] = {}
        for case in cases:
            if case.onset_date:
                date_str = case.onset_date.isoformat()
                onset_counts[date_str] = onset_counts.get(date_str, 0) + 1

        # Sort by date
        epi_curve = [
            {"date": d, "count": c}
            for d, c in sorted(onset_counts.items())
        ]

        # Calculate summary statistics
        total_cases = len(cases)
        hospitalized = sum(1 for c in cases if c.hospitalized)
        interviewed = sum(1 for c in cases if c.was_interviewed)
        has_location = sum(1 for c in cases if c.reported_exposure_location_id is not None)

        onset_dates = [c.onset_date for c in cases if c.onset_date]
        earliest = min(onset_dates) if onset_dates else None
        latest = max(onset_dates) if onset_dates else None
        duration_days = (latest - earliest).days if earliest and latest else 0

        summary = {
            "total_cases": total_cases,
            "hospitalized_cases": hospitalized,
            "hospitalization_rate": round(hospitalized / total_cases * 100, 1) if total_cases > 0 else 0.0,
            "interviewed_cases": interviewed,
            "interview_rate": round(interviewed / total_cases * 100, 1) if total_cases > 0 else 0.0,
            "cases_with_exposure_location": has_location,
            "exposure_location_rate": round(has_location / total_cases * 100, 1) if total_cases > 0 else 0.0,
            "earliest_onset": earliest.isoformat() if earliest else None,
            "latest_onset": latest.isoformat() if latest else None,
            "outbreak_duration_days": duration_days,
        }

        # Calculate per-node case counts
        node_counts: Dict[str, Dict[str, Any]] = {}
        for case in cases:
            location_id = case.exposure_location_id
            if location_id:
                location_str = str(location_id)
                if location_str not in node_counts:
                    node_counts[location_str] = {
                        "case_count": 0,
                        "hospitalized_count": 0,
                    }
                node_counts[location_str]["case_count"] += 1
                if case.hospitalized:
                    node_counts[location_str]["hospitalized_count"] += 1

        # Build node case count list with node details
        node_case_counts = []
        for node_id_str, counts in node_counts.items():
            node_name = "Unknown"
            node_type = "unknown"

            if network:
                try:
                    node_uuid = UUID(node_id_str)
                    node = network.get_node(node_uuid)
                    if node:
                        node_type = node.node_type.value
                        if hasattr(node, 'store_name'):
                            node_name = f"{node.store_name} #{node.store_number}"
                        elif hasattr(node, 'facility_name'):
                            node_name = node.facility_name
                        else:
                            node_name = str(node_uuid)[:8]
                except (ValueError, KeyError):
                    pass

            node_case_counts.append({
                "node_id": node_id_str,
                "node_name": node_name,
                "node_type": node_type,
                "case_count": counts["case_count"],
                "hospitalized_count": counts["hospitalized_count"],
            })

        # Sort by case count descending
        node_case_counts.sort(key=lambda x: x["case_count"], reverse=True)

        return {
            "epi_curve": epi_curve,
            "summary": summary,
            "node_case_counts": node_case_counts,
        }


# Global service instance
simulation_service = SimulationService()
