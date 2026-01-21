import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function AboutPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center py-6">
        <h1 className="text-3xl font-bold mb-2">About This Simulation</h1>
        <p className="text-muted-foreground">
          FSMA 204 Outbreak Traceability Simulation
        </p>
      </div>

      {/* Author & Credits */}
      <Card>
        <CardHeader>
          <CardTitle>Author & Development</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p>
            This simulation was developed by <strong>Ben Miller, PhD, MPH</strong>, based on the FDA's
            "FSMA Final Rule on Requirements for Additional Traceability Records for Certain Foods"
            regulation and Dr. Miller's subject matter expertise in food safety, epidemiology, and
            outbreak investigation.
          </p>
          <p>
            This tool was developed using <strong>Claude Code</strong> (Anthropic's AI coding assistant).
          </p>
          <p>
            Questions about this simulation can be directed to Dr. Miller at{' '}
            <a href="mailto:mill1543@umn.edu" className="text-blue-600 hover:underline">
              mill1543@umn.edu
            </a>
          </p>
        </CardContent>
      </Card>

      {/* Purpose */}
      <Card>
        <CardHeader>
          <CardTitle>Purpose</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p>
            This simulation is designed to demonstrate the impact of traceability record-keeping
            practices on foodborne illness outbreak investigations. It compares two scenarios:
          </p>
          <ul className="list-disc pl-6 space-y-2">
            <li>
              <strong>Deterministic Tracking:</strong> Supply chain participants maintain exact
              lot code records as required by FSMA 204, enabling precise traceback from consumer
              to source.
            </li>
            <li>
              <strong>Probabilistic Tracking:</strong> Distribution centers use calculated lot
              codes based on inventory date windows rather than exact traceability records,
              creating uncertainty in traceback investigations.
            </li>
          </ul>
          <p>
            Users can explore how differences in traceability practices affect investigation scope,
            the ability to identify contamination sources, and the number of products and facilities
            that must be examined during an outbreak response.
          </p>
        </CardContent>
      </Card>

      {/* Supply Chain Model */}
      <Card>
        <CardHeader>
          <CardTitle>Supply Chain Model</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p>The simulation models a simplified food supply chain with the following node types:</p>
          <div className="grid grid-cols-2 gap-4 my-4">
            <div className="flex items-center gap-2">
              <Badge className="bg-green-500">Farm</Badge>
              <span className="text-sm">Produces fresh cucumbers with unique lot codes per harvest</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge className="bg-blue-500">Packer</Badge>
              <span className="text-sm">Receives and packs cucumbers, maintains lot code linkage</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge className="bg-purple-500">Processor</Badge>
              <span className="text-sm">Transforms cucumbers into cucumber salad (new TLC assigned)</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge className="bg-amber-500">Distribution Center</Badge>
              <span className="text-sm">Receives, stores, and ships products to retailers</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge className="bg-pink-500">Deli</Badge>
              <span className="text-sm">In-store deli that prepares and serves salads</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge className="bg-cyan-500">Retailer</Badge>
              <span className="text-sm">Retail store where consumers purchase products</span>
            </div>
          </div>
          <p>
            Product flows from farms through packers, to distribution centers, and finally to
            retailers/delis. Processors transform fresh cucumbers into cucumber salad, creating
            a new Traceability Lot Code (TLC) at the transformation point.
          </p>
          <p>
            Supply chain nodes are assigned geographic coordinates based on real US cities in
            agricultural regions (California, Arizona) and distribution hubs across the country.
            Transit times between nodes are calculated using the Haversine formula for great-circle
            distance, providing realistic product flow timing.
          </p>
        </CardContent>
      </Card>

      {/* Key Concepts */}
      <Card>
        <CardHeader>
          <CardTitle>Key FSMA 204 Concepts</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-semibold">Traceability Lot Code (TLC)</h4>
            <p className="text-sm text-muted-foreground">
              A unique identifier assigned to a lot of food that links all Critical Tracking Events
              (CTEs) for that lot. TLCs are assigned at Initial Packing (farms) or Transformation
              (processors) events.
            </p>
          </div>
          <div>
            <h4 className="font-semibold">Traceability Lot Code Source (TLCS)</h4>
            <p className="text-sm text-muted-foreground">
              The Global Location Number (GLN) of the physical location where the TLC was assigned.
              The TLCS does not change as product moves through the supply chain unless the product
              goes through a Transformation CTE.
            </p>
          </div>
          <div>
            <h4 className="font-semibold">Critical Tracking Events (CTEs)</h4>
            <p className="text-sm text-muted-foreground">
              Key events in the supply chain that require traceability records: Harvesting, Cooling,
              Initial Packing, Shipping, Receiving, and Transformation.
            </p>
          </div>
          <div>
            <h4 className="font-semibold">Key Data Elements (KDEs)</h4>
            <p className="text-sm text-muted-foreground">
              Required data that must be recorded at each CTE, including TLC, TLCS, product
              description, quantity, location identifiers, and dates/times.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Simulation Mechanics */}
      <Card>
        <CardHeader>
          <CardTitle>Simulation Mechanics</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-semibold">Contamination Seeding</h4>
            <p className="text-sm text-muted-foreground">
              A randomly selected farm is designated as the contamination source. All lots harvested
              from that farm during the contamination period are marked as contaminated. Contamination
              propagates forward through the supply chain following product flow.
            </p>
          </div>
          <div>
            <h4 className="font-semibold">Inventory Management</h4>
            <p className="text-sm text-muted-foreground">
              Distribution centers use a configurable inventory strategy for calculating probabilistic
              lot code assignments. In deterministic mode, exact TLCs are always tracked. In probabilistic
              mode, the DC calculates which TLCs COULD have been shipped based on the selected strategy:
            </p>
            <ul className="text-sm text-muted-foreground list-disc pl-6 mt-2 space-y-1">
              <li><strong>FIFO:</strong> First-In-First-Out - older inventory is assumed more likely to ship first</li>
              <li><strong>LIFO:</strong> Last-In-First-Out - newer inventory is assumed more likely to ship first</li>
              <li><strong>All-in-Window:</strong> All TLCs received within the date window are equally likely</li>
              <li><strong>Inventory Weighted:</strong> Probability weighted by remaining inventory quantity</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold">Case Generation</h4>
            <p className="text-sm text-muted-foreground">
              Consumer exposures occur at retailers and delis. Cases are generated based on pathogen
              characteristics (attack rate, incubation period) from consumers who purchased contaminated
              products. Interview success rate determines how many cases provide useful exposure information.
            </p>
          </div>
          <div>
            <h4 className="font-semibold">Traceback Investigation</h4>
            <p className="text-sm text-muted-foreground">
              Starting from interviewed cases, the simulation traces back through the supply chain
              to identify potential source farms. In deterministic mode, exact paths are known.
              In probabilistic mode, multiple possible paths must be considered with associated
              probabilities.
            </p>
          </div>
          <div>
            <h4 className="font-semibold">Supply Chain Timing</h4>
            <p className="text-sm text-muted-foreground">
              The simulation models realistic time delays throughout the supply chain to allow
              inventory to accumulate at distribution centers, making inventory management strategies
              (FIFO, LIFO, etc.) more meaningful. Timing components include:
            </p>
            <ul className="text-sm text-muted-foreground list-disc pl-6 mt-2 space-y-1">
              <li><strong>Distance-based transit:</strong> Transit times are calculated using geographic distance between nodes (Haversine formula), with a base time plus additional hours per 100 miles</li>
              <li><strong>Post-harvest cooling:</strong> Products are held at farms after harvest for cooling before shipping (default: 12 hours)</li>
              <li><strong>DC inspection:</strong> Quality assurance inspection time at distribution centers before products are available for outbound shipping (default: 6 hours)</li>
              <li><strong>Retail stocking:</strong> Time between receiving at retail and shelf availability for consumers (default: 4 hours)</li>
              <li><strong>Business hours:</strong> Shipments occur during business hours (6 AM - 6 PM)</li>
            </ul>
            <p className="text-sm text-muted-foreground mt-2">
              The default 90-day simulation period allows realistic product flow through the supply
              chain and accounts for investigation timeframes needed by public health investigators
              to identify cases and conduct traceback investigations.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Assumptions */}
      <Card>
        <CardHeader>
          <CardTitle>Model Assumptions</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="list-disc pl-6 space-y-2 text-sm">
            <li>
              All supply chain participants (except DCs in probabilistic mode) maintain perfect
              traceability records with no errors or missing data.
            </li>
            <li>
              Product flow follows a simplified linear path: Farm → Packer → DC → Retailer/Deli,
              or Farm → Packer → Processor → DC → Retailer/Deli.
            </li>
            <li>
              Contamination is binary at the farm level - all product from the contaminated farm
              during the contamination period is considered contaminated.
            </li>
            <li>
              Distribution centers use the selected inventory strategy (FIFO, LIFO, All-in-Window,
              or Inventory Weighted) consistently for probabilistic lot code calculations.
            </li>
            <li>
              The date window for probabilistic lot code calculation is configurable but uniform
              across all distribution centers.
            </li>
            <li>
              Interview success rate applies uniformly to all cases.
            </li>
            <li>
              Consumer purchasing patterns are randomly distributed across retail endpoints.
            </li>
            <li>
              All product is sold and consumed within the simulation period (no waste/spoilage).
            </li>
            <li>
              Transit times include configurable variance (±20% by default) to simulate real-world
              variability in shipping times.
            </li>
            <li>
              Hold times (cooling, inspection, stocking) are configurable but applied uniformly
              across all nodes of the same type.
            </li>
          </ul>
        </CardContent>
      </Card>

      {/* Limitations */}
      <Card>
        <CardHeader>
          <CardTitle>Limitations</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="list-disc pl-6 space-y-2 text-sm">
            <li>
              This is a simplified model and does not capture the full complexity of real-world
              food supply chains, which may include multiple distribution tiers, cross-docking,
              returns, and more complex product transformations.
            </li>
            <li>
              The simulation assumes a single contamination source. Real outbreaks may involve
              multiple sources or cross-contamination events.
            </li>
            <li>
              Pathogen characteristics (attack rate, incubation period) are simplified and may
              not reflect the variability seen in actual outbreaks.
            </li>
            <li>
              The model does not account for environmental sampling, product testing, or other
              investigation tools that complement traceability records.
            </li>
            <li>
              Recall scope and economic impacts are not modeled.
            </li>
            <li>
              The simulation does not model regulatory inspection processes or enforcement actions.
            </li>
            <li>
              While the simulation uses real US city coordinates and distance-based transit times,
              actual transportation routes, traffic, and logistics complexities are not modeled.
            </li>
          </ul>
        </CardContent>
      </Card>

      {/* Monte Carlo */}
      <Card>
        <CardHeader>
          <CardTitle>Monte Carlo Simulation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p>
            The Monte Carlo feature runs multiple iterations of the simulation with different
            random seeds to generate statistical distributions of outcomes. This allows users to:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-sm">
            <li>
              Estimate the expected scope expansion when using probabilistic vs. deterministic
              tracking across many scenarios.
            </li>
            <li>
              Calculate confidence intervals for key metrics like farm scope expansion, TLC
              scope expansion, and source identification accuracy.
            </li>
            <li>
              Compare the statistical significance of differences between tracking modes using
              McNemar's test.
            </li>
            <li>
              Visualize the distribution of outcomes through histograms and summary statistics.
            </li>
          </ul>
        </CardContent>
      </Card>

      {/* Metrics Explained */}
      <Card>
        <CardHeader>
          <CardTitle>Key Metrics Explained</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-semibold">Farm Scope Expansion</h4>
            <p className="text-sm text-muted-foreground">
              The ratio of farms identified in the probabilistic investigation to farms identified
              in the deterministic investigation. Higher values indicate more farms must be
              investigated due to traceability uncertainty.
            </p>
          </div>
          <div>
            <h4 className="font-semibold">TLC Scope Expansion</h4>
            <p className="text-sm text-muted-foreground">
              The ratio of Traceability Lot Codes that must be traced in probabilistic mode vs.
              deterministic mode. Indicates the additional lot-level investigation burden.
            </p>
          </div>
          <div>
            <h4 className="font-semibold">TLCS Expansion</h4>
            <p className="text-sm text-muted-foreground">
              The ratio of unique Traceability Lot Code Sources (locations where TLCs were assigned)
              in probabilistic vs. deterministic investigations.
            </p>
          </div>
          <div>
            <h4 className="font-semibold">Source Identification Outcome</h4>
            <p className="text-sm text-muted-foreground">
              Whether the investigation correctly identified the actual contamination source farm.
              Outcomes are: Yes (correct with clear margin), No (incorrect), or Inconclusive
              (top farms too close in probability to distinguish).
            </p>
          </div>
          <div>
            <h4 className="font-semibold">Source Rank</h4>
            <p className="text-sm text-muted-foreground">
              The position of the actual source farm when farms are ranked by investigation
              convergence score. Rank 1 means the true source was the top suspect.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <Card className="border-amber-200 bg-amber-50">
        <CardHeader>
          <CardTitle className="text-amber-800">Disclaimer</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-amber-900">
          <p>
            This simulation is provided for informational and educational purposes only.
            This tool may produce outputs that are inaccurate or contain errors.
          </p>
          <p>
            The simulation is provided "AS IS" without warranty of any kind, express or implied,
            including but not limited to the warranties of merchantability, fitness for a particular
            purpose, and noninfringement. In no event shall the authors or copyright holders be
            liable for any claim, damages, or other liability arising from the use of this simulation.
          </p>
          <p>
            Users should independently verify any outputs and should not rely solely on this
            simulation for regulatory compliance, food safety decisions, or any other critical purposes.
            This simulation does not constitute legal, regulatory, or professional advice.
          </p>
        </CardContent>
      </Card>

      {/* Footer */}
      <div className="text-center py-6 text-sm text-muted-foreground">
        <p>
          Questions or feedback? Contact{' '}
          <a href="mailto:mill1543@umn.edu" className="text-blue-600 hover:underline">
            mill1543@umn.edu
          </a>
        </p>
      </div>
    </div>
  )
}
