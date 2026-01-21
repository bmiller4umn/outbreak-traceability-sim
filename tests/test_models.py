"""
Tests for FSMA 204 traceability data models.

These tests verify that the data models correctly represent
the cucumber outbreak scenario and support both deterministic
and calculated lot code tracking.
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest

from outbreak_traceability_sim.models.base import (
    Location,
    ProductDescription,
    Quantity,
    ProductCategory,
    UnitOfMeasure,
    ContactInfo,
)
from outbreak_traceability_sim.models.nodes import (
    Farm,
    Packer,
    DistributionCenter,
    Processor,
    Retailer,
    GrowingArea,
    LotCodeAssignmentMode,
    CalculatedLotCodeMethod,
)
from outbreak_traceability_sim.models.events import (
    HarvestingCTE,
    ShippingCTE,
    ReceivingCTE,
    TransformationCTE,
    TransformationInput,
)
from outbreak_traceability_sim.models.lots import (
    LotTracker,
    LotGraph,
    TrackingMode,
    OutbreakScenario,
)


@pytest.fixture
def sample_location():
    """Create a sample location for testing."""
    return Location(
        gln="1234567890123",
        name="Test Farm",
        street_address="123 Farm Road",
        city="Salinas",
        state="CA",
        zip_code="93901",
    )


@pytest.fixture
def sample_contact():
    """Create a sample contact for testing."""
    return ContactInfo(
        name="John Farmer",
        phone="831-555-1234",
        email="john@testfarm.com",
    )


@pytest.fixture
def cucumber_product():
    """Create a cucumber product description."""
    return ProductDescription(
        category=ProductCategory.FRESH_CUCUMBERS,
        commodity="Cucumbers",
        variety="Persian",
        description="Fresh Persian Cucumbers",
    )


@pytest.fixture
def cucumber_salad_product():
    """Create a cucumber salad product description."""
    return ProductDescription(
        category=ProductCategory.CUCUMBER_SALAD,
        commodity="Cucumber Salad",
        description="Deli Cucumber Salad",
    )


class TestLocation:
    """Tests for Location model."""

    def test_location_creation(self, sample_location):
        """Test basic location creation."""
        assert sample_location.gln == "1234567890123"
        assert sample_location.state == "CA"

    def test_location_identifier_gln_preferred(self, sample_location):
        """Test that GLN is preferred identifier."""
        assert sample_location.identifier == "1234567890123"

    def test_location_identifier_fallback(self):
        """Test identifier fallback when no GLN."""
        loc = Location(
            name="Test Location",
            street_address="123 Test St",
            city="Test City",
            state="CA",
            zip_code="12345",
        )
        assert loc.identifier == "Test Location"


class TestFarm:
    """Tests for Farm supply chain node."""

    def test_farm_creation(self, sample_location, sample_contact):
        """Test farm node creation."""
        farm = Farm(
            location=sample_location,
            contact=sample_contact,
            farm_name="Green Valley Farm",
            responsible_party=sample_contact,
            commodities_grown=[ProductCategory.FRESH_CUCUMBERS],
        )
        assert farm.farm_name == "Green Valley Farm"
        assert ProductCategory.FRESH_CUCUMBERS in farm.commodities_grown

    def test_farm_lot_code_generation(self, sample_location, sample_contact):
        """Test deterministic lot code generation at farm."""
        farm = Farm(
            location=sample_location,
            contact=sample_contact,
            farm_name="Green Valley Farm",
            responsible_party=sample_contact,
            growing_areas=[
                GrowingArea(area_id="FIELD_A", name="Field A"),
            ],
        )

        tlc = farm.generate_lot_code(date(2024, 3, 15), "FIELD_A")
        assert "20240315" in tlc
        assert "FIELD_A" in tlc


class TestDistributionCenter:
    """Tests for Distribution Center with lot code modes."""

    def test_dc_deterministic_mode(self, sample_location, sample_contact):
        """Test DC in deterministic (full compliance) mode."""
        dc = DistributionCenter(
            location=sample_location,
            contact=sample_contact,
            facility_name="Central DC",
            responsible_party=sample_contact,
            assignment_mode=LotCodeAssignmentMode.DETERMINISTIC,
        )
        assert dc.assignment_mode == LotCodeAssignmentMode.DETERMINISTIC

    def test_dc_calculated_mode(self, sample_location, sample_contact):
        """Test DC in calculated lot code mode."""
        dc = DistributionCenter(
            location=sample_location,
            contact=sample_contact,
            facility_name="Central DC",
            responsible_party=sample_contact,
            assignment_mode=LotCodeAssignmentMode.CALCULATED,
            calculated_method=CalculatedLotCodeMethod.FIFO_DATE_RANGE,
            date_window_days=7,
        )
        assert dc.assignment_mode == LotCodeAssignmentMode.CALCULATED
        assert dc.calculated_method == CalculatedLotCodeMethod.FIFO_DATE_RANGE


class TestLotTracker:
    """Tests for lot tracking system."""

    def test_lot_creation(self):
        """Test creating a lot in the tracker."""
        tracker = LotTracker()
        node_id = uuid4()
        location_id = uuid4()

        lot = tracker.create_lot(
            tlc="FARM-20240315-FIELD_A",
            node_id=node_id,
            location_id=location_id,
            product_category="fresh_cucumbers",
            product_description="Fresh Persian Cucumbers",
            quantity_value=1000,
            quantity_unit="lbs",
        )

        assert lot.tlc == "FARM-20240315-FIELD_A"
        assert tracker.total_lots_created == 1

    def test_deterministic_lot_linkage(self):
        """Test deterministic lot linking (full compliance)."""
        tracker = LotTracker(default_mode=TrackingMode.DETERMINISTIC)
        node_id = uuid4()
        location_id = uuid4()

        # Create source lot
        source_lot = tracker.create_lot(
            tlc="FARM-001",
            node_id=node_id,
            location_id=location_id,
            product_category="fresh_cucumbers",
            product_description="Fresh Cucumbers",
            quantity_value=1000,
            quantity_unit="lbs",
        )

        # Create destination lot with deterministic link
        dest_lot = tracker.create_lot(
            tlc="DC-001",
            node_id=node_id,
            location_id=location_id,
            product_category="fresh_cucumbers",
            product_description="Fresh Cucumbers",
            quantity_value=500,
            quantity_unit="lbs",
            source_tlcs=["FARM-001"],
        )

        # Traceback should find exact source
        traceback = tracker.traceback_from_retail("DC-001")
        assert "FARM-001" in traceback.tlc_probabilities
        assert traceback.tlc_probabilities["FARM-001"] == 1.0

    def test_probabilistic_lot_linkage(self):
        """Test probabilistic lot linking (calculated scenario)."""
        tracker = LotTracker(default_mode=TrackingMode.PROBABILISTIC)
        node_id = uuid4()
        location_id = uuid4()

        # Create multiple source lots
        for i in range(3):
            tracker.create_lot(
                tlc=f"FARM-{i:03d}",
                node_id=node_id,
                location_id=location_id,
                product_category="fresh_cucumbers",
                product_description="Fresh Cucumbers",
                quantity_value=1000,
                quantity_unit="lbs",
            )

        # Create destination with probabilistic links
        tracker.create_lot(
            tlc="DC-001",
            node_id=node_id,
            location_id=location_id,
            product_category="fresh_cucumbers",
            product_description="Fresh Cucumbers",
            quantity_value=500,
            quantity_unit="lbs",
            source_probabilities={
                "FARM-000": 0.4,
                "FARM-001": 0.35,
                "FARM-002": 0.25,
            },
        )

        # Traceback should include all possible sources
        traceback = tracker.graph.traceback("DC-001", min_probability=0.0)
        assert len(traceback.probabilistic_tlcs) == 3

    def test_traceback_scope_comparison(self):
        """Test comparison of traceback scope between modes."""
        tracker = LotTracker()
        node_id = uuid4()
        location_id = uuid4()

        # Create multiple farm lots
        for i in range(5):
            tracker.create_lot(
                tlc=f"FARM-{i:03d}",
                node_id=node_id,
                location_id=location_id,
                product_category="fresh_cucumbers",
                product_description="Fresh Cucumbers",
                quantity_value=1000,
                quantity_unit="lbs",
            )

        # Create DC lot with both deterministic and probabilistic links
        tracker.create_lot(
            tlc="DC-001",
            node_id=node_id,
            location_id=location_id,
            product_category="fresh_cucumbers",
            product_description="Fresh Cucumbers",
            quantity_value=500,
            quantity_unit="lbs",
            source_tlcs=["FARM-000"],  # Deterministic: only this one
            source_probabilities={
                "FARM-001": 0.3,  # Calculated: these are also possible
                "FARM-002": 0.2,
            },
        )

        comparison = tracker.compare_traceback_scope("DC-001")

        # Deterministic should have smaller scope
        assert comparison["deterministic_scope"] < comparison["probabilistic_scope"]
        assert comparison["scope_expansion_factor"] > 1.0


class TestOutbreakScenario:
    """Tests for outbreak scenario configuration."""

    def test_scenario_creation(self):
        """Test outbreak scenario configuration."""
        scenario = OutbreakScenario(
            name="Cucumber Salmonella Outbreak",
            description="Contaminated cucumbers from Farm A",
            contaminated_farm_id=uuid4(),
            contaminated_tlc="FARM-A-20240301-FIELD1",
            contamination_date=date(2024, 3, 1),
            contamination_source_description="Irrigation water contamination",
            first_illness_date=date(2024, 3, 8),
            days_to_detection=7,
        )

        assert scenario.name == "Cucumber Salmonella Outbreak"
        assert scenario.days_to_detection == 7

    def test_scope_expansion_metrics(self):
        """Test scope expansion metric calculations."""
        scenario = OutbreakScenario(
            name="Test Outbreak",
            description="Test",
            contaminated_farm_id=uuid4(),
            contaminated_tlc="TEST-001",
            contamination_date=date(2024, 3, 1),
            contamination_source_description="Test contamination",
            first_illness_date=date(2024, 3, 8),
            deterministic_farms_in_scope=2,
            deterministic_tlcs_in_scope=5,
            calculated_farms_in_scope=8,
            calculated_tlcs_in_scope=25,
        )

        assert scenario.farm_scope_expansion == 4.0
        assert scenario.tlc_scope_expansion == 5.0
