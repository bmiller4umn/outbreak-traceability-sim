"""
Outbreak simulation runner.

Orchestrates the complete simulation pipeline from network creation
through contamination, exposure, case generation, and investigation.
Produces comparison metrics between deterministic and calculated lot code modes.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from uuid import UUID
import random

from ..models.nodes import LotCodeAssignmentMode, CalculatedLotCodeMethod
from ..models.lots import LotGraph

from .network import NetworkConfig, NetworkBuilder, SupplyChainNetwork
from .contamination import ContaminationSeeder, ContaminationEvent
from .flow import ProductFlowSimulator
from .exposure import ExposureGenerator, CaseGenerator, IllnessCase
from .investigation import InvestigationEngine, compare_investigation_modes, InvestigationTimingConfig
from .timing import TimingConfig


@dataclass
class SimulationConfig:
    """Configuration for outbreak simulation."""
    # Time period
    start_date: date = field(default_factory=lambda: date.today() - timedelta(days=30))
    end_date: date = field(default_factory=date.today)

    # Network configuration
    num_farms: int = 5
    num_packers: int = 2
    num_distribution_centers: int = 3
    num_retailers: int = 20
    retailers_with_delis_pct: float = 0.3

    # Contamination configuration
    contamination_start_offset_days: int = 5  # Days after simulation start
    contamination_duration_days: int = 7
    contamination_rate: float = 1.0
    pathogen: str = "Salmonella"

    # Exposure configuration
    daily_customers_per_retailer: int = 50
    cucumber_purchase_rate: float = 0.15
    deli_consumption_rate: float = 0.05

    # Case configuration
    infection_rate: float = 0.3
    receipt_retention_rate: float = 0.0  # Consumers don't retain TLC info for bulk produce

    # Investigation parameters (realistic outbreak investigation model)
    interview_success_rate: float = 0.7  # Fraction of cases successfully interviewed
    record_collection_window_days: int = 14  # Days of records FDA requests from retailers
    num_investigators: int = 5  # Number of investigators assigned to traceback

    # Random seed
    random_seed: Optional[int] = None

    # Timing configuration for realistic supply chain delays
    timing_config: Optional[TimingConfig] = None


@dataclass
class SimulationMetrics:
    """Metrics from a single simulation run."""
    # Network metrics
    num_farms: int = 0
    num_retailers: int = 0
    num_delis: int = 0

    # Flow metrics
    lots_created: int = 0
    shipments: int = 0
    deterministic_links: int = 0
    probabilistic_links: int = 0

    # Contamination metrics
    source_farm_name: str = ""
    contaminated_source_tlcs: int = 0
    contaminated_downstream_tlcs: int = 0

    # Case metrics
    total_exposures: int = 0
    actual_exposures: int = 0
    total_cases: int = 0
    cases_hospitalized: int = 0


@dataclass
class ComparisonResult:
    """Results comparing deterministic vs calculated lot code scenarios."""
    # Scenario info
    scenario_name: str = ""
    dc_tracking_mode: str = ""

    # Metrics from this run
    metrics: SimulationMetrics = field(default_factory=SimulationMetrics)

    # Investigation results - deterministic
    det_farms_in_scope: int = 0
    det_tlcs_in_scope: int = 0
    det_tlcs_locations: int = 0  # TLCS - unique locations where TLCs were created
    det_traceback_paths: int = 0
    det_primary_suspect: str = ""
    det_primary_suspect_confidence: float = 0.0  # Confidence score for primary suspect
    det_identification_outcome: str = "inconclusive"  # "yes", "no", or "inconclusive"
    det_source_rank: int = 0
    det_top_two_margin: float = 0.0  # Confidence gap between #1 and #2

    # Investigation results - probabilistic
    prob_farms_in_scope: int = 0
    prob_tlcs_in_scope: int = 0
    prob_tlcs_locations: int = 0  # TLCS - unique locations where TLCs were created
    prob_traceback_paths: int = 0
    prob_primary_suspect: str = ""
    prob_primary_suspect_confidence: float = 0.0  # Confidence score for primary suspect
    prob_identification_outcome: str = "inconclusive"  # "yes", "no", or "inconclusive"
    prob_source_rank: int = 0
    prob_top_two_margin: float = 0.0  # Confidence gap between #1 and #2

    # Expansion factors
    farm_scope_expansion: float = 1.0
    tlc_scope_expansion: float = 1.0
    path_expansion: float = 1.0

    # Investigation timing estimates
    det_investigation_timing: Optional[dict] = None
    prob_investigation_timing: Optional[dict] = None
    timing_expansion: float = 1.0

    # Probability distribution over farms
    farm_probabilities: dict[str, float] = field(default_factory=dict)


class OutbreakSimulator:
    """
    Main simulation runner for outbreak scenarios.

    Runs complete simulation pipeline and produces comparison metrics
    between full compliance (deterministic) and calculated lot code modes.
    """

    def __init__(self, config: Optional[SimulationConfig] = None):
        """
        Initialize the simulator.

        Args:
            config: Simulation configuration
        """
        self.config = config or SimulationConfig()

        if self.config.random_seed is not None:
            random.seed(self.config.random_seed)

        # Components (initialized during run)
        self.network: Optional[SupplyChainNetwork] = None
        self.lot_graph: Optional[LotGraph] = None
        self.seeder: Optional[ContaminationSeeder] = None
        self.flow_sim: Optional[ProductFlowSimulator] = None
        self.exposure_gen: Optional[ExposureGenerator] = None
        self.case_gen: Optional[CaseGenerator] = None
        self.cases: list[IllnessCase] = []

        # Contamination source (for ground truth comparison)
        self.contaminated_farm_id: Optional[UUID] = None

    def _build_network(self, dc_mode: LotCodeAssignmentMode) -> SupplyChainNetwork:
        """Build supply chain network with specified DC tracking mode."""
        network_config = NetworkConfig(
            num_farms=self.config.num_farms,
            num_packers=self.config.num_packers,
            num_distribution_centers=self.config.num_distribution_centers,
            num_retailers=self.config.num_retailers,
            retailers_with_delis_pct=self.config.retailers_with_delis_pct,
            dc_tracking_mode=dc_mode,
            dc_calculated_method=CalculatedLotCodeMethod.FIFO_DATE_RANGE,
            dc_date_window_days=7,
            random_seed=self.config.random_seed,
        )

        builder = NetworkBuilder(network_config)
        return builder.build()

    def _simulate_flow(self, network: SupplyChainNetwork) -> ProductFlowSimulator:
        """Simulate product flow through network."""
        flow_sim = ProductFlowSimulator(
            network,
            self.config.start_date,
            self.config.end_date,
            random_seed=self.config.random_seed,
            timing_config=self.config.timing_config,
        )
        flow_sim.run_simulation()
        return flow_sim

    def _seed_contamination(
        self,
        network: SupplyChainNetwork,
        lot_graph: LotGraph,
        lot_metadata: dict[str, dict],
        farm_id: Optional[UUID] = None
    ) -> ContaminationSeeder:
        """Seed contamination at a specific or random farm."""
        seeder = ContaminationSeeder(lot_graph)

        # Select farm (use specified or random)
        if farm_id is not None:
            selected_farm_id = farm_id
        else:
            farm_ids = list(network.farms.keys())
            selected_farm_id = random.choice(farm_ids)
        selected_farm = network.farms[selected_farm_id]

        # Calculate contamination dates - start early to ensure propagation
        contam_start = self.config.start_date
        contam_end = self.config.start_date + timedelta(
            days=self.config.contamination_duration_days
        )

        # Create contamination event
        seeder.create_contamination_event(
            farm_id=selected_farm_id,
            farm_name=selected_farm.farm_name,
            start_date=contam_start,
            end_date=contam_end,
            pathogen=self.config.pathogen,
            contamination_source="Irrigation water contamination",
            contamination_rate=self.config.contamination_rate,
        )

        # Seed and propagate
        seeder.seed_contamination(lot_metadata)
        seeder.propagate_contamination()

        self.contaminated_farm_id = selected_farm_id
        return seeder

    def _generate_cases(
        self,
        network: SupplyChainNetwork,
        lot_graph: LotGraph,
        contamination: dict[str, float],
        node_inventory: dict
    ) -> tuple[ExposureGenerator, CaseGenerator, list[IllnessCase]]:
        """Generate exposures and illness cases."""
        # Generate exposures
        exposure_gen = ExposureGenerator(
            network,
            lot_graph,
            contamination,
            random_seed=self.config.random_seed,
        )

        exposures = exposure_gen.generate_exposures(
            node_inventory,
            self.config.start_date,
            self.config.end_date,
            daily_customers_per_retailer=self.config.daily_customers_per_retailer,
            cucumber_purchase_rate=self.config.cucumber_purchase_rate,
            deli_consumption_rate=self.config.deli_consumption_rate,
        )

        # Generate cases using interview-based model
        case_gen = CaseGenerator(
            pathogen=self.config.pathogen,
            random_seed=self.config.random_seed,
        )
        case_gen.configure_pathogen(infection_rate=self.config.infection_rate)

        cases = case_gen.generate_cases(
            exposures,
            interview_success_rate=self.config.interview_success_rate,
        )

        return exposure_gen, case_gen, cases

    def run_scenario(
        self,
        scenario_name: str,
        dc_mode: LotCodeAssignmentMode,
        farm_index: int = 0
    ) -> ComparisonResult:
        """
        Run a single scenario with specified DC tracking mode.

        Args:
            scenario_name: Name for this scenario
            dc_mode: Distribution center lot code tracking mode
            farm_index: Index of farm to contaminate (for consistency)

        Returns:
            Comparison result with all metrics
        """
        # Build network
        network = self._build_network(dc_mode)
        self.network = network

        # Simulate product flow
        flow_sim = self._simulate_flow(network)
        self.flow_sim = flow_sim
        self.lot_graph = flow_sim.lot_graph

        # Get farm ID by index for consistency
        farm_ids = list(network.farms.keys())
        farm_id = farm_ids[farm_index % len(farm_ids)]

        # Seed contamination at specified farm
        seeder = self._seed_contamination(
            network,
            flow_sim.lot_graph,
            flow_sim.lot_metadata,
            farm_id=farm_id
        )
        self.seeder = seeder

        # Generate cases
        exposure_gen, case_gen, cases = self._generate_cases(
            network,
            flow_sim.lot_graph,
            seeder.contamination_propagation,
            flow_sim.node_inventory
        )
        self.exposure_gen = exposure_gen
        self.case_gen = case_gen
        self.cases = cases

        # Build metrics
        metrics = SimulationMetrics(
            num_farms=len(network.farms),
            num_retailers=len(network.retailers),
            num_delis=len(network.delis),
            lots_created=flow_sim.total_lots_created,
            shipments=len(flow_sim.shipments),
            deterministic_links=flow_sim.deterministic_lot_links,
            probabilistic_links=flow_sim.probabilistic_lot_links,
            source_farm_name=seeder.contamination_events[0].farm_name if seeder.contamination_events else "",
            contaminated_source_tlcs=len(seeder.contaminated_source_tlcs),
            contaminated_downstream_tlcs=len(seeder.contamination_propagation),
            total_exposures=len(exposure_gen.exposures),
            actual_exposures=len(exposure_gen.get_exposed_consumers()),
            total_cases=len(cases),
            cases_hospitalized=len([c for c in cases if c.hospitalized]),
        )

        # Run comparative investigation
        investigation_timing_config = InvestigationTimingConfig(
            num_investigators=self.config.num_investigators
        )
        comparison = compare_investigation_modes(
            network,
            flow_sim.lot_graph,
            cases,
            self.contaminated_farm_id,
            record_collection_window_days=self.config.record_collection_window_days,
            node_inventory=flow_sim.node_inventory,
            tlc_shipment_map=flow_sim.tlc_shipment_map,
            timing_config=investigation_timing_config
        )

        # Get probability distribution
        prob_engine = InvestigationEngine(
            network,
            flow_sim.lot_graph,
            is_probabilistic=True,
            record_collection_window_days=self.config.record_collection_window_days,
            node_inventory=flow_sim.node_inventory,
            tlc_shipment_map=flow_sim.tlc_shipment_map
        )
        farm_probs = prob_engine.get_farm_probability_distribution(cases)

        # Build result
        result = ComparisonResult(
            scenario_name=scenario_name,
            dc_tracking_mode=dc_mode.value,
            metrics=metrics,

            det_farms_in_scope=comparison["deterministic"]["farms_in_scope"],
            det_tlcs_in_scope=comparison["deterministic"]["tlcs_in_scope"],
            det_tlcs_locations=comparison["deterministic"]["tlcs_locations"],
            det_traceback_paths=comparison["deterministic"]["traceback_paths"],
            det_primary_suspect=comparison["deterministic"]["primary_suspect"],
            det_primary_suspect_confidence=comparison["deterministic"]["primary_suspect_confidence"],
            det_identification_outcome=comparison["deterministic"]["identification_outcome"],
            det_source_rank=comparison["deterministic"]["source_rank"],
            det_top_two_margin=comparison["deterministic"]["top_two_margin"],

            prob_farms_in_scope=comparison["probabilistic"]["farms_in_scope"],
            prob_tlcs_in_scope=comparison["probabilistic"]["tlcs_in_scope"],
            prob_tlcs_locations=comparison["probabilistic"]["tlcs_locations"],
            prob_traceback_paths=comparison["probabilistic"]["traceback_paths"],
            prob_primary_suspect=comparison["probabilistic"]["primary_suspect"],
            prob_primary_suspect_confidence=comparison["probabilistic"]["primary_suspect_confidence"],
            prob_identification_outcome=comparison["probabilistic"]["identification_outcome"],
            prob_source_rank=comparison["probabilistic"]["source_rank"],
            prob_top_two_margin=comparison["probabilistic"]["top_two_margin"],

            farm_scope_expansion=comparison["comparison"]["farm_scope_expansion"],
            tlc_scope_expansion=comparison["comparison"]["tlc_scope_expansion"],
            path_expansion=comparison["comparison"]["path_expansion"],

            det_investigation_timing=comparison["deterministic"].get("investigation_timing"),
            prob_investigation_timing=comparison["probabilistic"].get("investigation_timing"),
            timing_expansion=comparison["comparison"].get("timing_expansion", 1.0),

            farm_probabilities=farm_probs,
        )

        return result

    def run_comparison(self) -> dict:
        """
        Run full comparison between deterministic and calculated investigation modes.

        This implements a counterfactual comparison:
        - ONE simulation with calculated lot codes at DCs (realistic scenario)
        - TWO investigation modes on the SAME outbreak:
          - Deterministic: What if we had perfect lot tracking? (ground truth)
          - Probabilistic: What can we determine with calculated lot codes?

        Returns:
            Dictionary with complete comparison results
        """
        if self.config.random_seed is not None:
            random.seed(self.config.random_seed)

        # Run ONE simulation with calculated lot codes at DCs
        # This creates a lot graph with BOTH deterministic (ground truth) and
        # probabilistic (estimated) lot linkages
        result = self.run_scenario(
            "Outbreak Simulation",
            LotCodeAssignmentMode.CALCULATED,
            farm_index=0
        )

        # The comparison already happened in run_scenario via compare_investigation_modes()
        # which runs BOTH deterministic and probabilistic investigation on the SAME lot graph

        # Calculate expansion factors
        farm_expansion = (
            result.prob_farms_in_scope / max(1, result.det_farms_in_scope)
        )
        tlc_expansion = (
            result.prob_tlcs_in_scope / max(1, result.det_tlcs_in_scope)
        )
        tlcs_location_expansion = (
            result.prob_tlcs_locations / max(1, result.det_tlcs_locations)
        )
        path_expansion = (
            result.prob_traceback_paths / max(1, result.det_traceback_paths)
        )

        # The actual contaminated farm (ground truth)
        source_farm = result.metrics.source_farm_name

        return {
            "configuration": {
                "simulation_period": {
                    "start": self.config.start_date.isoformat(),
                    "end": self.config.end_date.isoformat(),
                },
                "network": {
                    "farms": self.config.num_farms,
                    "packers": self.config.num_packers,
                    "distribution_centers": self.config.num_distribution_centers,
                    "retailers": self.config.num_retailers,
                },
                "pathogen": self.config.pathogen,
            },
            "scenarios": {
                "deterministic": {
                    "name": "Full Compliance (Deterministic)",
                    "dc_mode": "deterministic",
                    "cases": result.metrics.total_cases,
                    "farms_in_scope": result.det_farms_in_scope,
                    "tlcs_in_scope": result.det_tlcs_in_scope,
                    "tlcs_locations": result.det_tlcs_locations,  # TLCS
                    "traceback_paths": result.det_traceback_paths,
                    "primary_suspect": result.det_primary_suspect,
                    "identification_outcome": result.det_identification_outcome,
                    "source_rank": result.det_source_rank,
                    "top_two_margin": result.det_top_two_margin,
                    "actual_source": source_farm,
                    "lot_links": {
                        "deterministic": result.metrics.deterministic_links,
                        "probabilistic": result.metrics.probabilistic_links,
                    },
                    "investigation_timing": result.det_investigation_timing,
                },
                "calculated": {
                    "name": "Calculated Lot Codes",
                    "dc_mode": "calculated",
                    "cases": result.metrics.total_cases,
                    "farms_in_scope": result.prob_farms_in_scope,
                    "tlcs_in_scope": result.prob_tlcs_in_scope,
                    "tlcs_locations": result.prob_tlcs_locations,  # TLCS
                    "traceback_paths": result.prob_traceback_paths,
                    "primary_suspect": result.prob_primary_suspect,
                    "identification_outcome": result.prob_identification_outcome,
                    "source_rank": result.prob_source_rank,
                    "top_two_margin": result.prob_top_two_margin,
                    "actual_source": source_farm,
                    "lot_links": {
                        "deterministic": result.metrics.deterministic_links,
                        "probabilistic": result.metrics.probabilistic_links,
                    },
                    "farm_probabilities": result.farm_probabilities,
                    "investigation_timing": result.prob_investigation_timing,
                },
            },
            "metrics": {
                "source_farm": source_farm,
                "lots_created_deterministic": result.metrics.lots_created,
                "lots_created_calculated": result.metrics.lots_created,
                "farm_scope_expansion": farm_expansion,
                "tlc_scope_expansion": tlc_expansion,
                "tlcs_location_expansion": tlcs_location_expansion,  # TLCS expansion
                "path_expansion": path_expansion,
                "timing_expansion": result.timing_expansion,
            },
            "conclusion": self._generate_conclusion_single(result, farm_expansion, tlc_expansion),
        }

    def _generate_conclusion(
        self,
        det_result: ComparisonResult,
        calc_result: ComparisonResult,
        farm_expansion: float,
        tlc_expansion: float
    ) -> dict:
        """Generate conclusion comparing the two scenarios."""
        det_outcome = det_result.det_identification_outcome
        calc_outcome = calc_result.prob_identification_outcome

        accuracy_note = self._get_accuracy_note(det_outcome, calc_outcome, calc_result)

        return {
            "deterministic_outcome": det_outcome,
            "calculated_outcome": calc_outcome,
            "farm_scope_expansion": farm_expansion,
            "tlc_scope_expansion": tlc_expansion,
            "impact_summary": (
                f"With calculated lot codes at distribution centers, the investigation "
                f"scope expanded by {farm_expansion:.1f}x for farms and {tlc_expansion:.1f}x for TLCs. "
                f"{accuracy_note}"
            ),
        }

    def _generate_conclusion_single(
        self,
        result: ComparisonResult,
        farm_expansion: float,
        tlc_expansion: float
    ) -> dict:
        """Generate conclusion from a single simulation with both investigation modes."""
        det_outcome = result.det_identification_outcome
        calc_outcome = result.prob_identification_outcome

        accuracy_note = self._get_accuracy_note(det_outcome, calc_outcome, result)

        return {
            "deterministic_outcome": det_outcome,
            "calculated_outcome": calc_outcome,
            "farm_scope_expansion": farm_expansion,
            "tlc_scope_expansion": tlc_expansion,
            "impact_summary": (
                f"Comparing investigation outcomes for the SAME outbreak: "
                f"With calculated lot codes at distribution centers, the investigation "
                f"scope expanded by {farm_expansion:.1f}x for farms and {tlc_expansion:.1f}x for TLCs. "
                f"{accuracy_note}"
            ),
        }

    def _get_accuracy_note(
        self,
        det_outcome: str,
        calc_outcome: str,
        result: ComparisonResult
    ) -> str:
        """Generate accuracy note based on identification outcomes."""
        if det_outcome == "yes" and calc_outcome == "yes":
            return "The correct source was conclusively identified in both investigation modes."
        elif det_outcome == "yes" and calc_outcome == "inconclusive":
            return (
                f"With full lot code compliance, the source was conclusively identified. "
                f"With calculated lot codes, the result was inconclusive (margin: {result.prob_top_two_margin:.3f})."
            )
        elif det_outcome == "yes" and calc_outcome == "no":
            return (
                f"With full lot code compliance, the source was correctly identified. "
                f"With calculated lot codes, the wrong source was identified "
                f"(actual source ranked #{result.prob_source_rank})."
            )
        elif det_outcome == "inconclusive" and calc_outcome == "yes":
            return (
                f"With full lot code compliance, the result was inconclusive. "
                f"With calculated lot codes, the correct source was identified."
            )
        elif det_outcome == "inconclusive" and calc_outcome == "inconclusive":
            return "Both investigation modes produced inconclusive results (top farms too close in score)."
        elif det_outcome == "inconclusive" and calc_outcome == "no":
            return (
                f"With full lot code compliance, the result was inconclusive. "
                f"With calculated lot codes, the wrong source was identified."
            )
        elif det_outcome == "no" and calc_outcome == "yes":
            return (
                f"Deterministic tracking identified the wrong source. "
                f"Calculated lot codes correctly identified the source."
            )
        elif det_outcome == "no" and calc_outcome == "inconclusive":
            return (
                f"Deterministic tracking identified the wrong source. "
                f"With calculated lot codes, the result was inconclusive."
            )
        else:  # both "no"
            return "Neither investigation mode correctly identified the source."


def run_outbreak_simulation(
    num_farms: int = 5,
    num_retailers: int = 20,
    simulation_days: int = 90,
    random_seed: Optional[int] = None
) -> dict:
    """
    Convenience function to run a complete outbreak simulation.

    Args:
        num_farms: Number of farms in network
        num_retailers: Number of retailers in network
        simulation_days: Duration of simulation in days
        random_seed: Random seed for reproducibility

    Returns:
        Complete comparison results
    """
    config = SimulationConfig(
        start_date=date.today() - timedelta(days=simulation_days),
        end_date=date.today(),
        num_farms=num_farms,
        num_retailers=num_retailers,
        random_seed=random_seed,
    )

    simulator = OutbreakSimulator(config)
    return simulator.run_comparison()
