import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'

export default function UserGuidePage() {
  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">User Guide</h1>
        <p className="text-muted-foreground">
          Comprehensive documentation for the FSMA 204 Outbreak Traceability Simulation
        </p>
      </div>

      {/* Table of Contents */}
      <Card>
        <CardHeader>
          <CardTitle>Contents</CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="list-decimal list-inside space-y-1 text-sm">
            <li><a href="#overview" className="text-blue-600 hover:underline">Overview &amp; Purpose</a></li>
            <li><a href="#simulation-structure" className="text-blue-600 hover:underline">Simulation Structure</a></li>
            <li><a href="#network-config" className="text-blue-600 hover:underline">Network Configuration Settings</a></li>
            <li><a href="#contamination-config" className="text-blue-600 hover:underline">Contamination Settings</a></li>
            <li><a href="#inventory-strategy" className="text-blue-600 hover:underline">DC Inventory Strategy</a></li>
            <li><a href="#investigation-params" className="text-blue-600 hover:underline">Investigation Parameters</a></li>
            <li><a href="#timing-config" className="text-blue-600 hover:underline">Supply Chain Timing</a></li>
            <li><a href="#product-flow" className="text-blue-600 hover:underline">How Product Flow Works</a></li>
            <li><a href="#contamination-spread" className="text-blue-600 hover:underline">How Contamination Spreads</a></li>
            <li><a href="#case-generation" className="text-blue-600 hover:underline">Case Exposure &amp; Detection</a></li>
            <li><a href="#investigation-process" className="text-blue-600 hover:underline">The Investigation Process</a></li>
            <li><a href="#understanding-results" className="text-blue-600 hover:underline">Understanding Results</a></li>
            <li><a href="#examples" className="text-blue-600 hover:underline">Worked Examples</a></li>
          </ol>
        </CardContent>
      </Card>

      {/* Section 1: Overview */}
      <section id="overview">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">1.</span>
              Overview &amp; Purpose
            </CardTitle>
          </CardHeader>
          <CardContent className="prose prose-sm max-w-none space-y-4">
            <p>
              This simulation demonstrates the impact of <strong>FSMA 204 traceability requirements</strong> on
              outbreak investigations. Specifically, it compares two scenarios:
            </p>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                <h4 className="font-semibold text-green-700 mb-2">Full Compliance (Deterministic)</h4>
                <p className="text-sm">
                  All supply chain participants maintain exact, 1:1 linkages between incoming and outgoing
                  Traceability Lot Codes (TLCs). When product arrives at a Distribution Center, the exact
                  TLCs that go into each outgoing shipment are recorded.
                </p>
              </div>
              <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                <h4 className="font-semibold text-orange-700 mb-2">Calculated Lot Codes (Probabilistic)</h4>
                <p className="text-sm">
                  Distribution Centers use "calculated" lot codes based on what <em>might</em> have been
                  in a shipment. They know which TLCs were in inventory during a date window, but can't
                  prove exactly which ones went into each outgoing shipment.
                </p>
              </div>
            </div>

            <h4 className="font-semibold mt-4">Why This Matters</h4>
            <p>
              During a foodborne illness outbreak, FDA investigators must trace contaminated product back
              to its source. With <strong>deterministic tracking</strong>, each traceback follows a single,
              clear path. With <strong>calculated lot codes</strong>, investigators must consider multiple
              possible paths, dramatically expanding the scope of the investigation.
            </p>

            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="font-semibold text-blue-700 mb-2">Key Metrics</h4>
              <ul className="text-sm space-y-1">
                <li><strong>Farms in Scope:</strong> Number of farms that must be investigated</li>
                <li><strong>TLCs in Scope:</strong> Number of lot codes that must be analyzed</li>
                <li><strong>Traceback Paths:</strong> Number of possible routes through the supply chain</li>
                <li><strong>Investigation Time:</strong> Estimated calendar days to complete investigation</li>
                <li><strong>Source Identification:</strong> Whether the correct source farm was identified</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Section 2: Simulation Structure */}
      <section id="simulation-structure">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">2.</span>
              Simulation Structure
            </CardTitle>
          </CardHeader>
          <CardContent className="prose prose-sm max-w-none space-y-4">
            <p>The simulation models a complete fresh produce supply chain with five tiers:</p>

            <div className="overflow-x-auto">
              <table className="min-w-full text-sm border">
                <thead className="bg-muted">
                  <tr>
                    <th className="border p-2 text-left">Tier</th>
                    <th className="border p-2 text-left">Node Type</th>
                    <th className="border p-2 text-left">Role</th>
                    <th className="border p-2 text-left">TLC Behavior</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="border p-2">1</td>
                    <td className="border p-2 font-medium">Farm</td>
                    <td className="border p-2">Grows and harvests produce</td>
                    <td className="border p-2">Creates original TLCs at harvest</td>
                  </tr>
                  <tr className="bg-muted/50">
                    <td className="border p-2">2</td>
                    <td className="border p-2 font-medium">Packer</td>
                    <td className="border p-2">Washes, grades, packs produce</td>
                    <td className="border p-2">Maintains 1:1 TLC linkage (always deterministic)</td>
                  </tr>
                  <tr>
                    <td className="border p-2">3</td>
                    <td className="border p-2 font-medium">Distribution Center</td>
                    <td className="border p-2">Aggregates and distributes to retailers</td>
                    <td className="border p-2">
                      <Badge variant="outline" className="mr-1">Key Node</Badge>
                      Deterministic OR Calculated tracking
                    </td>
                  </tr>
                  <tr className="bg-muted/50">
                    <td className="border p-2">4</td>
                    <td className="border p-2 font-medium">Retailer</td>
                    <td className="border p-2">Sells to consumers (produce section)</td>
                    <td className="border p-2">Receives TLCs, consumers purchase</td>
                  </tr>
                  <tr>
                    <td className="border p-2">4</td>
                    <td className="border p-2 font-medium">Deli</td>
                    <td className="border p-2">Prepares food for consumption</td>
                    <td className="border p-2">Receives TLCs, processes into meals</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <h4 className="font-semibold mt-4">Supply Chain Flow</h4>
            <div className="p-4 bg-gray-50 rounded-lg font-mono text-sm">
              Farm → Packer → Distribution Center → Retailer/Deli → Consumer
            </div>

            <h4 className="font-semibold mt-4">Simulation Timeline</h4>
            <p>
              The simulation runs for a configurable number of days (default: 90). During this period:
            </p>
            <ol className="list-decimal list-inside space-y-1">
              <li>Farms harvest produce daily and create TLCs</li>
              <li>Product flows through the supply chain with realistic transit times</li>
              <li>One farm becomes contaminated for a specified duration</li>
              <li>Contaminated product spreads through the network</li>
              <li>Consumers are exposed and some become ill</li>
              <li>Cases are reported and investigated</li>
            </ol>
          </CardContent>
        </Card>
      </section>

      {/* Section 3: Network Configuration */}
      <section id="network-config">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">3.</span>
              Network Configuration Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="prose prose-sm max-w-none space-y-4">
            <p>These settings control the size and structure of the supply chain network.</p>

            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="farms">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Badge>Farms</Badge>
                    <span>Number of source farms (1-20)</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <p><strong>Default:</strong> 5 farms</p>
                  <p><strong>What it controls:</strong> The number of produce farms in the simulation. One of these farms will be randomly selected as the contamination source.</p>
                  <p><strong>Impact on results:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>More farms = more potential sources to investigate</li>
                    <li>More farms = harder to identify the correct source (more "noise")</li>
                    <li>Fewer farms = clearer convergence patterns but less realistic</li>
                  </ul>
                  <p><strong>Realistic range:</strong> For a regional outbreak involving cucumbers, 5-15 farms is typical. National outbreaks might involve more.</p>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="packers">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Badge>Packers</Badge>
                    <span>Number of packing facilities (1-10)</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <p><strong>Default:</strong> 2 packers</p>
                  <p><strong>What it controls:</strong> Packing houses that receive produce from farms, wash/grade it, and ship to distribution centers.</p>
                  <p><strong>Impact on results:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>Packers maintain deterministic (1:1) TLC linkage</li>
                    <li>More packers = more distribution of product</li>
                    <li>Each packer serves multiple farms and ships to multiple DCs</li>
                  </ul>
                  <p><strong>Assumption:</strong> Packers always maintain exact traceability (required by FSMA 204).</p>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="dcs">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Badge>Distribution Centers</Badge>
                    <span>Number of DCs (1-10)</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <p><strong>Default:</strong> 3 distribution centers</p>
                  <p><strong>What it controls:</strong> Regional distribution centers that aggregate product from packers and distribute to retailers.</p>
                  <p><strong>Impact on results:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>DCs are the <strong>key comparison point</strong> - they can use deterministic or calculated lot codes</li>
                    <li>More DCs = product distributed across more pathways</li>
                    <li>DCs hold inventory and ship based on configured strategy (FIFO, LIFO, etc.)</li>
                  </ul>
                  <p><strong>Key insight:</strong> The DC is where traceability often breaks down in practice. Some DCs can prove exactly which incoming lots went into each outgoing shipment; others can only provide a range of possibilities.</p>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="retailers">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Badge>Retailers</Badge>
                    <span>Number of retail locations (5-100)</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <p><strong>Default:</strong> 20 retailers</p>
                  <p><strong>What it controls:</strong> Grocery stores and supermarkets where consumers purchase produce.</p>
                  <p><strong>Impact on results:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>More retailers = more potential exposure points</li>
                    <li>More retailers = more cases but more data for convergence analysis</li>
                    <li>A percentage of retailers also have delis (configured separately)</li>
                  </ul>
                  <p><strong>Investigation note:</strong> These are the "Points of Service" (POS) where FDA requests records during an outbreak.</p>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>
      </section>

      {/* Section 4: Contamination Settings */}
      <section id="contamination-config">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">4.</span>
              Contamination Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="prose prose-sm max-w-none space-y-4">
            <p>These settings control the outbreak scenario - how contamination occurs and spreads.</p>

            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="rate">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Badge variant="destructive">Contamination Rate</Badge>
                    <span>Percentage of product contaminated (0-100%)</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <p><strong>Default:</strong> 100%</p>
                  <p><strong>What it controls:</strong> What percentage of product harvested during the contamination period is actually contaminated.</p>
                  <p><strong>Impact on results:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>100% = All product from the contaminated farm during the outbreak period is contaminated</li>
                    <li>Lower rates = Some lots escape contamination, creating more uncertainty</li>
                    <li>Lower rates = Fewer cases, harder to identify source through convergence</li>
                  </ul>
                  <p><strong>Real-world note:</strong> Contamination is often sporadic. A field might have one contaminated irrigation source affecting only part of the harvest.</p>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="duration">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Badge variant="destructive">Contamination Duration</Badge>
                    <span>Days the source is contaminated (1-14)</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <p><strong>Default:</strong> 7 days</p>
                  <p><strong>What it controls:</strong> How many consecutive days the source farm produces contaminated product.</p>
                  <p><strong>Impact on results:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>Longer duration = More contaminated TLCs enter the supply chain</li>
                    <li>Longer duration = More cases, stronger convergence signal</li>
                    <li>Shorter duration = Fewer TLCs, product may not reach all retailers</li>
                  </ul>
                  <p><strong>Real-world range:</strong> Most produce contamination events last 1-2 weeks before being detected or naturally resolving.</p>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="sim-days">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Badge>Simulation Days</Badge>
                    <span>Total simulation period (7-180 days)</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <p><strong>Default:</strong> 90 days</p>
                  <p><strong>What it controls:</strong> The total time period simulated, from first harvest to end of data collection.</p>
                  <p><strong>Impact on results:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>Longer simulation = More product flow, more realistic inventory accumulation at DCs</li>
                    <li>Longer simulation = Contamination event has more time to propagate through network</li>
                    <li>Contamination starts early in the simulation to ensure propagation</li>
                  </ul>
                  <p><strong>Recommendation:</strong> Use at least 60 days to allow for realistic inventory buildup and product flow through all tiers.</p>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>
      </section>

      {/* Section 5: Inventory Strategy */}
      <section id="inventory-strategy">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">5.</span>
              DC Inventory Strategy
            </CardTitle>
          </CardHeader>
          <CardContent className="prose prose-sm max-w-none space-y-4">
            <p>
              These settings control how Distribution Centers select which TLCs to include when they
              ship product to retailers. This is <strong>critical</strong> for the calculated lot code scenario.
            </p>

            <div className="p-4 bg-amber-50 rounded-lg border border-amber-200 mb-4">
              <h4 className="font-semibold text-amber-800 mb-2">Why Inventory Strategy Matters</h4>
              <p className="text-sm">
                In the <strong>deterministic</strong> scenario, DCs know exactly which TLCs went into each
                shipment. In the <strong>calculated</strong> scenario, DCs must estimate based on their
                inventory management practices. The strategy determines which TLCs are considered
                "potentially included" in a shipment.
              </p>
            </div>

            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="fifo">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-blue-500">FIFO</Badge>
                    <span>First-In-First-Out (Recommended)</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <p><strong>How it works:</strong> DCs ship the oldest inventory first. When calculating which TLCs might have been in a shipment, they consider TLCs received within the date window, weighted toward older product.</p>
                  <p><strong>Probability calculation:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>Older TLCs get higher probability of being shipped</li>
                    <li>Probability decreases linearly with receipt date</li>
                    <li>TLCs outside the date window get 0% probability</li>
                  </ul>
                  <p><strong>Real-world relevance:</strong> FIFO is standard practice for perishables to minimize spoilage. Most DCs claim to follow FIFO, making this the most realistic default.</p>
                  <div className="p-3 bg-gray-100 rounded mt-2 font-mono text-xs">
                    Example: Date window = 7 days<br/>
                    TLC received 7 days ago: ~100% probability<br/>
                    TLC received 4 days ago: ~57% probability<br/>
                    TLC received 1 day ago: ~14% probability
                  </div>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="lifo">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-purple-500">LIFO</Badge>
                    <span>Last-In-First-Out</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <p><strong>How it works:</strong> DCs ship the newest inventory first. This is less common for perishables but might occur due to warehouse layout or convenience.</p>
                  <p><strong>Probability calculation:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>Newer TLCs get higher probability of being shipped</li>
                    <li>Probability decreases for older product</li>
                  </ul>
                  <p><strong>Impact on investigation:</strong> LIFO creates different patterns of TLC distribution compared to FIFO, potentially affecting which farms appear in scope.</p>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="all-in-window">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-gray-500">All in Window</Badge>
                    <span>Equal probability for all TLCs in date range</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <p><strong>How it works:</strong> All TLCs that were in inventory during the date window are considered equally likely to have been shipped.</p>
                  <p><strong>Probability calculation:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>Every TLC in the window: equal probability</li>
                    <li>No weighting by age or quantity</li>
                  </ul>
                  <p><strong>Use case:</strong> Worst-case scenario for traceability - DC cannot provide any information about shipping priorities.</p>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="inventory-weighted">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-green-600">Inventory Weighted</Badge>
                    <span>Weighted by remaining quantity</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <p><strong>How it works:</strong> TLCs with larger remaining quantities are more likely to have been included in a shipment.</p>
                  <p><strong>Probability calculation:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>Probability proportional to inventory quantity</li>
                    <li>TLC with 1000 lbs remaining is twice as likely as one with 500 lbs</li>
                  </ul>
                  <p><strong>Use case:</strong> Represents DCs that draw from multiple pallets proportionally rather than emptying one before starting another.</p>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="date-window">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">Date Window</Badge>
                    <span>Days of inventory considered (1-30)</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <p><strong>Default:</strong> 7 days</p>
                  <p><strong>What it controls:</strong> When a DC uses calculated lot codes, this is the window of receipt dates they consider when determining which TLCs might have been in a shipment.</p>
                  <p><strong>Impact on results:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>Wider window = More TLCs potentially included = Greater scope expansion</li>
                    <li>Narrower window = Fewer TLCs considered = Less expansion but might miss actual TLCs</li>
                  </ul>
                  <p><strong>Real-world note:</strong> This reflects how long perishable product typically remains in DC inventory. For cucumbers, 5-10 days is realistic.</p>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>
      </section>

      {/* Section 6: Investigation Parameters */}
      <section id="investigation-params">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">6.</span>
              Investigation Parameters
            </CardTitle>
          </CardHeader>
          <CardContent className="prose prose-sm max-w-none space-y-4">
            <p>
              These settings model how the FDA conducts outbreak investigations - from interviewing
              patients to requesting records and analyzing traceback data.
            </p>

            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="interview-rate">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Badge>Interview Success Rate</Badge>
                    <span>Percentage of cases interviewed (10-100%)</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <p><strong>Default:</strong> 70%</p>
                  <p><strong>What it controls:</strong> The percentage of illness cases where epidemiologists successfully interview the patient and obtain:
                  </p>
                  <ul className="list-disc list-inside ml-4">
                    <li>Where they likely purchased/consumed the product (exposure location)</li>
                    <li>Approximate date of purchase</li>
                  </ul>
                  <p><strong>Why interviews fail:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>Patient cannot be reached</li>
                    <li>Patient cannot recall where they purchased the product</li>
                    <li>Patient consumed product at multiple locations</li>
                    <li>Interview not completed before investigation closes</li>
                  </ul>
                  <p><strong>Impact on results:</strong> Higher interview rates provide more data points for convergence analysis. Cases without successful interviews cannot contribute to the traceback.</p>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="record-window">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Badge>FDA Record Collection Window</Badge>
                    <span>Days of records requested (7-30)</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <p><strong>Default:</strong> 14 days</p>
                  <p><strong>What it controls:</strong> When FDA contacts a retail location identified by a patient, they request records for a window of time around the estimated purchase date.</p>
                  <p><strong>Why a window is needed:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>Patients often cannot recall exact purchase dates</li>
                    <li>Incubation periods vary (1-7 days for most pathogens)</li>
                    <li>Product may have been stored before consumption</li>
                  </ul>
                  <p><strong>Impact on results:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>Wider window = More TLCs captured = Better chance of finding actual source but more noise</li>
                    <li>Narrower window = Fewer TLCs but might miss the actual contaminated lot</li>
                  </ul>
                  <p><strong>Calculation:</strong> Window is centered on estimated purchase date (±half the window days).</p>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="investigators">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Badge>Investigators Assigned</Badge>
                    <span>Team size for traceback (1-20)</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <p><strong>Default:</strong> 5 investigators</p>
                  <p><strong>What it controls:</strong> The number of FDA/state investigators assigned to the traceback portion of the investigation.</p>
                  <p><strong>Assumptions:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>Each investigator works 6 hours per day of "direct work" (excluding meetings, travel, etc.)</li>
                    <li>Analysis tasks (TLC review, traceback, convergence) can be parallelized across the team</li>
                    <li>Record request wait time is NOT parallelizable (it's calendar time waiting for responses)</li>
                  </ul>
                  <p><strong>Impact on results:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>More investigators = Faster analysis of TLCs and paths</li>
                    <li>More investigators = Shorter calendar time to complete investigation</li>
                    <li>Record request delays remain constant regardless of team size</li>
                  </ul>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>
      </section>

      {/* Section 7: Supply Chain Timing */}
      <section id="timing-config">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">7.</span>
              Supply Chain Timing
            </CardTitle>
          </CardHeader>
          <CardContent className="prose prose-sm max-w-none space-y-4">
            <p>
              These advanced settings control realistic time delays as product moves through the supply
              chain. They affect how inventory accumulates at DCs and the timing of consumer exposures.
            </p>

            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="transit-speed">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">Transit Speed Factor</Badge>
                    <span>Multiplier for transit times (0.5x-2.0x)</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <p><strong>Default:</strong> 1.0x (normal speed)</p>
                  <p><strong>What it controls:</strong> Multiplier applied to all transit times (Farm→Packer, Packer→DC, DC→Retailer).</p>
                  <p><strong>Base transit times:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>Farm to Packer: 4 hours base + distance factor</li>
                    <li>Packer to DC: 8 hours base + distance factor</li>
                    <li>DC to Retailer: 4 hours base + distance factor</li>
                  </ul>
                  <p><strong>Use cases:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>0.5x = Fast/local supply chain (same-region distribution)</li>
                    <li>1.0x = Normal regional distribution</li>
                    <li>2.0x = Slow/long-distance national distribution</li>
                  </ul>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="cooling">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">Post-Harvest Cooling</Badge>
                    <span>Hold time after harvest (0-48 hours)</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <p><strong>Default:</strong> 12 hours</p>
                  <p><strong>What it controls:</strong> Time product is held at the farm for field heat removal before shipping to packer.</p>
                  <p><strong>Why this matters:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>Fresh produce must be rapidly cooled after harvest</li>
                    <li>Cucumbers are typically hydro-cooled or forced-air cooled</li>
                    <li>This delay affects when product enters the supply chain</li>
                  </ul>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="dc-inspection">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">DC QA Inspection</Badge>
                    <span>Hold time at DC before available (0-24 hours)</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <p><strong>Default:</strong> 6 hours</p>
                  <p><strong>What it controls:</strong> Time product is held at the Distribution Center for quality inspection before being available for outbound shipment.</p>
                  <p><strong>Real-world process:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>Receiving inspection (temperature, condition)</li>
                    <li>Documentation verification</li>
                    <li>Assignment to inventory location</li>
                    <li>System entry and availability</li>
                  </ul>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="retail-stocking">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">Retail Stocking Delay</Badge>
                    <span>Time to reach shelf (0-24 hours)</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <p><strong>Default:</strong> 4 hours</p>
                  <p><strong>What it controls:</strong> Time between product arriving at a retail store and being available for consumer purchase.</p>
                  <p><strong>Factors included:</strong></p>
                  <ul className="list-disc list-inside ml-4">
                    <li>Receiving and documentation</li>
                    <li>Movement to back room storage</li>
                    <li>Stocking on produce floor</li>
                  </ul>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>
      </section>

      {/* Section 8: Product Flow */}
      <section id="product-flow">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">8.</span>
              How Product Flow Works
            </CardTitle>
          </CardHeader>
          <CardContent className="prose prose-sm max-w-none space-y-4">
            <p>
              Understanding how product moves through the supply chain is essential to understanding
              why calculated lot codes create traceability challenges.
            </p>

            <h4 className="font-semibold">Step 1: Farm Harvest</h4>
            <div className="p-4 bg-green-50 rounded-lg border-l-4 border-green-500 mb-4">
              <p className="text-sm mb-2">Each day during the simulation, farms harvest produce:</p>
              <ul className="text-sm list-disc list-inside">
                <li>A new <strong>Traceability Lot Code (TLC)</strong> is created for each harvest batch</li>
                <li>TLC format: <code>FARM-001-2024-01-15-001</code> (Farm ID, date, sequence)</li>
                <li>The TLC is linked to the <strong>TLCS</strong> (Traceability Lot Code Source) - the farm's GLN</li>
                <li>Product is held for cooling, then shipped to a packer</li>
              </ul>
            </div>

            <h4 className="font-semibold">Step 2: Packer Processing</h4>
            <div className="p-4 bg-blue-50 rounded-lg border-l-4 border-blue-500 mb-4">
              <p className="text-sm mb-2">Packers receive produce from multiple farms:</p>
              <ul className="text-sm list-disc list-inside">
                <li>Product is washed, graded, and packed</li>
                <li>Packer creates new TLCs but maintains <strong>1:1 linkage</strong> to source TLCs</li>
                <li>Each outgoing TLC is linked to exactly one incoming TLC</li>
                <li>This is <strong>always deterministic</strong> - no ambiguity</li>
              </ul>
            </div>

            <h4 className="font-semibold">Step 3: Distribution Center</h4>
            <div className="p-4 bg-amber-50 rounded-lg border-l-4 border-amber-500 mb-4">
              <p className="text-sm mb-2">DCs are the <strong>critical decision point</strong> for traceability:</p>

              <div className="grid grid-cols-2 gap-4 mt-3">
                <div className="p-3 bg-green-100 rounded">
                  <p className="font-semibold text-green-800 text-xs mb-1">Deterministic Mode</p>
                  <ul className="text-xs list-disc list-inside">
                    <li>DC tracks exactly which TLCs go into each shipment</li>
                    <li>Uses pick lists, lot scanning, or warehouse management systems</li>
                    <li>1:1 linkage maintained</li>
                  </ul>
                </div>
                <div className="p-3 bg-orange-100 rounded">
                  <p className="font-semibold text-orange-800 text-xs mb-1">Calculated Mode</p>
                  <ul className="text-xs list-disc list-inside">
                    <li>DC cannot prove exact TLCs in each shipment</li>
                    <li>Uses date window + inventory strategy to estimate</li>
                    <li>Multiple possible TLCs per shipment</li>
                  </ul>
                </div>
              </div>
            </div>

            <h4 className="font-semibold">Step 4: Retail Receipt</h4>
            <div className="p-4 bg-purple-50 rounded-lg border-l-4 border-purple-500 mb-4">
              <p className="text-sm mb-2">Retailers receive and stock product:</p>
              <ul className="text-sm list-disc list-inside">
                <li>TLCs are recorded at receiving</li>
                <li>Product is stocked in produce section or sent to deli</li>
                <li>Consumers purchase without TLC information (bulk produce)</li>
                <li>Retailer retains records for regulatory compliance</li>
              </ul>
            </div>

            <h4 className="font-semibold">TLC Linkage Example</h4>
            <div className="p-4 bg-gray-50 rounded-lg font-mono text-xs overflow-x-auto">
              <p className="text-sm font-sans font-semibold mb-2">Deterministic:</p>
              <p>Farm TLC: F001-0115-A → Packer TLC: P002-0116-X → DC TLC: D003-0117-Q → Retailer</p>
              <p className="text-green-600">✓ Single clear path</p>

              <p className="text-sm font-sans font-semibold mb-2 mt-4">Calculated (at DC):</p>
              <p>Farm TLC: F001-0115-A → Packer TLC: P002-0116-X → DC claims: "could be D003-0115-M (40%), D003-0116-N (35%), or D003-0117-O (25%)"</p>
              <p className="text-orange-600">⚠ Multiple possible paths, must investigate all</p>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Section 9: Contamination Spread */}
      <section id="contamination-spread">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">9.</span>
              How Contamination Spreads
            </CardTitle>
          </CardHeader>
          <CardContent className="prose prose-sm max-w-none space-y-4">
            <p>
              The simulation models contamination starting at a single farm and propagating through
              the supply chain via TLC linkages.
            </p>

            <h4 className="font-semibold">Contamination Event</h4>
            <ol className="list-decimal list-inside space-y-2 mb-4">
              <li>One farm is randomly selected as the contamination source</li>
              <li>For the specified duration (default: 7 days), that farm's harvest is contaminated</li>
              <li>Contaminated TLCs are marked in the lot graph</li>
              <li>Contamination rate determines what percentage of harvest is affected</li>
            </ol>

            <h4 className="font-semibold">Propagation Through Supply Chain</h4>
            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <p className="text-sm mb-2">Contamination follows TLC linkages downstream:</p>
              <ol className="text-sm list-decimal list-inside space-y-1">
                <li><strong>Farm → Packer:</strong> If source TLC is contaminated, linked packer TLC is contaminated</li>
                <li><strong>Packer → DC:</strong> Same logic - contamination follows the link</li>
                <li><strong>DC → Retailer:</strong> Same logic for deterministic mode</li>
              </ol>

              <p className="text-sm mt-3 mb-2"><strong>In calculated mode:</strong></p>
              <ul className="text-sm list-disc list-inside">
                <li>If ANY of the possible source TLCs is contaminated, the downstream TLC has contamination probability</li>
                <li>Probability = weighted average of source TLC contamination states</li>
              </ul>
            </div>

            <h4 className="font-semibold mt-4">Ground Truth vs. Investigation View</h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-gray-50 rounded">
                <p className="font-semibold text-sm mb-1">Simulation knows:</p>
                <ul className="text-xs list-disc list-inside">
                  <li>Which farm is actually contaminated</li>
                  <li>Which TLCs are actually contaminated</li>
                  <li>Exactly which consumers were exposed</li>
                </ul>
              </div>
              <div className="p-3 bg-gray-50 rounded">
                <p className="font-semibold text-sm mb-1">Investigation sees:</p>
                <ul className="text-xs list-disc list-inside">
                  <li>Reported illness cases</li>
                  <li>Interview responses (with error)</li>
                  <li>TLC records from retailers</li>
                  <li>Supply chain linkage data</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Section 10: Case Generation */}
      <section id="case-generation">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">10.</span>
              Case Exposure &amp; Detection
            </CardTitle>
          </CardHeader>
          <CardContent className="prose prose-sm max-w-none space-y-4">
            <p>
              The simulation models how consumers become exposed to contaminated product and how
              some of them become reported illness cases.
            </p>

            <h4 className="font-semibold">Consumer Exposure</h4>
            <ol className="list-decimal list-inside space-y-2 mb-4">
              <li><strong>Daily shopping:</strong> Simulated consumers visit retailers each day</li>
              <li><strong>Product selection:</strong> Some consumers purchase cucumbers (based on purchase rate)</li>
              <li><strong>TLC assignment:</strong> Consumer is assigned a TLC from the retailer's current inventory</li>
              <li><strong>Exposure determination:</strong> If the TLC is contaminated, the consumer is exposed</li>
            </ol>

            <h4 className="font-semibold">From Exposure to Illness</h4>
            <div className="p-4 bg-blue-50 rounded-lg mb-4">
              <p className="text-sm mb-2">Not everyone who is exposed becomes ill:</p>
              <ul className="text-sm list-disc list-inside space-y-1">
                <li><strong>Infection rate:</strong> ~30% of exposed individuals develop symptomatic illness</li>
                <li><strong>Incubation period:</strong> 1-7 days depending on pathogen (modeled but simplified)</li>
                <li><strong>Hospitalization:</strong> ~20% of cases require hospitalization</li>
              </ul>
            </div>

            <h4 className="font-semibold">Case Detection &amp; Reporting</h4>
            <div className="p-4 bg-amber-50 rounded-lg mb-4">
              <p className="text-sm mb-2">Cases enter the investigation through:</p>
              <ol className="text-sm list-decimal list-inside space-y-1">
                <li>Patient seeks medical care</li>
                <li>Healthcare provider orders stool culture</li>
                <li>Lab confirms pathogen and reports to public health</li>
                <li>Epidemiologist attempts to interview patient</li>
              </ol>
            </div>

            <h4 className="font-semibold">Interview Process</h4>
            <div className="grid grid-cols-1 gap-3">
              <div className="p-3 bg-green-50 rounded border-l-4 border-green-500">
                <p className="font-semibold text-sm text-green-800">Successful Interview (default: 70% of cases)</p>
                <ul className="text-xs list-disc list-inside mt-1">
                  <li>Patient recalls where they likely purchased cucumbers</li>
                  <li>Patient estimates purchase date (with some uncertainty)</li>
                  <li>This location becomes a "Point of Service" for traceback</li>
                </ul>
              </div>
              <div className="p-3 bg-red-50 rounded border-l-4 border-red-500">
                <p className="font-semibold text-sm text-red-800">Unsuccessful Interview</p>
                <ul className="text-xs list-disc list-inside mt-1">
                  <li>Patient cannot be reached, or</li>
                  <li>Patient cannot recall exposure location, or</li>
                  <li>Patient consumed product at multiple locations</li>
                  <li>Case cannot contribute to traceback</li>
                </ul>
              </div>
            </div>

            <h4 className="font-semibold mt-4">Important Assumption: No TLC Retention</h4>
            <div className="p-4 bg-gray-100 rounded">
              <p className="text-sm">
                For <strong>bulk produce</strong> like cucumbers, consumers do not retain TLC information.
                Unlike packaged goods with barcodes, bulk produce is selected from a bin without any
                identifying information transferred to the consumer. This is why the investigation must
                request records from the retailer for a date window, rather than tracing from a specific TLC.
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Section 11: Investigation Process */}
      <section id="investigation-process">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">11.</span>
              The Investigation Process
            </CardTitle>
          </CardHeader>
          <CardContent className="prose prose-sm max-w-none space-y-4">
            <p>
              This is the core of the simulation: modeling how FDA investigators trace back through
              the supply chain to identify the source of an outbreak.
            </p>

            <h4 className="font-semibold">Phase 1: Record Requests</h4>
            <div className="p-4 bg-blue-50 rounded-lg mb-4">
              <p className="text-sm mb-2"><strong>Process:</strong></p>
              <ol className="text-sm list-decimal list-inside space-y-1">
                <li>For each successfully interviewed case, FDA contacts the reported retail location</li>
                <li>FDA requests records for a date window around the estimated purchase date</li>
                <li>Retailer provides all TLCs that were present during that window</li>
              </ol>
              <p className="text-sm mt-2"><strong>Timing assumption:</strong></p>
              <ul className="text-sm list-disc list-inside">
                <li>48 hours turnaround per batch of requests</li>
                <li>10 locations can be contacted simultaneously</li>
                <li>This is calendar time (waiting), not parallelizable by adding investigators</li>
              </ul>
            </div>

            <h4 className="font-semibold">Phase 2: Traceback</h4>
            <div className="p-4 bg-green-50 rounded-lg mb-4">
              <p className="text-sm mb-2"><strong>For each TLC at each retail location:</strong></p>
              <ol className="text-sm list-decimal list-inside space-y-1">
                <li>Look up the TLC in the lot graph</li>
                <li>Find the upstream TLC(s) that link to it</li>
                <li>Repeat until reaching a farm-level TLC</li>
              </ol>

              <div className="grid grid-cols-2 gap-4 mt-3">
                <div className="p-3 bg-green-100 rounded">
                  <p className="font-semibold text-green-800 text-xs mb-1">Deterministic</p>
                  <p className="text-xs">Each TLC has exactly one upstream source. Follow the single path to the farm.</p>
                </div>
                <div className="p-3 bg-orange-100 rounded">
                  <p className="font-semibold text-orange-800 text-xs mb-1">Probabilistic</p>
                  <p className="text-xs">At the DC level, TLC may have multiple possible sources with probabilities. Must trace ALL possible paths.</p>
                </div>
              </div>
            </div>

            <h4 className="font-semibold">What is a "Traceback Path"?</h4>
            <div className="p-4 bg-gray-50 rounded-lg mb-4">
              <p className="text-sm mb-2">
                A <strong>traceback path</strong> is one complete chain of TLC linkages from a retail
                location back to a source farm:
              </p>
              <div className="font-mono text-xs p-2 bg-white rounded border">
                Retailer TLC → DC TLC → Packer TLC → Farm TLC
              </div>
              <p className="text-sm mt-2">
                <strong>Deterministic:</strong> ~1 path per TLC found at retail<br/>
                <strong>Probabilistic:</strong> Multiple paths per TLC (one for each possible DC source)
              </p>
              <p className="text-sm mt-2 text-amber-700">
                <strong>Path expansion</strong> is a key metric: if probabilistic mode has 5x more paths,
                investigators must trace 5x more supply chain routes.
              </p>
            </div>

            <h4 className="font-semibold">Phase 3: Convergence Analysis</h4>
            <div className="p-4 bg-purple-50 rounded-lg mb-4">
              <p className="text-sm mb-2">
                <strong>Convergence</strong> is when multiple independent traceback paths from different
                cases lead to the same farm. This is the primary signal for identifying the outbreak source.
              </p>
              <p className="text-sm mb-2"><strong>For each farm reached by tracebacks:</strong></p>
              <ul className="text-sm list-disc list-inside space-y-1">
                <li><strong>Cases converging:</strong> How many illness cases trace back to this farm?</li>
                <li><strong>Exclusive cases:</strong> How many cases trace ONLY to this farm?</li>
                <li><strong>Retail locations:</strong> How many different stores' cases converge here?</li>
              </ul>

              <h5 className="font-semibold text-sm mt-3">Confidence Scoring</h5>
              <p className="text-sm">Farms are ranked by a weighted confidence score:</p>
              <ul className="text-sm list-disc list-inside">
                <li>50%: Exclusive cases (strongest evidence)</li>
                <li>30%: Total case coverage</li>
                <li>15%: Location diversity</li>
                <li>5%: Path probability (for probabilistic mode)</li>
              </ul>
            </div>

            <h4 className="font-semibold">Phase 4: Farm Verification</h4>
            <div className="p-4 bg-amber-50 rounded-lg mb-4">
              <p className="text-sm">
                Top candidate farms are verified through on-site inspection, environmental sampling,
                and record review. The simulation estimates 16 hours per farm verification.
              </p>
            </div>

            <h4 className="font-semibold">Identification Outcomes</h4>
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 bg-green-100 rounded text-center">
                <p className="font-semibold text-green-800 text-sm">Yes</p>
                <p className="text-xs">Correct source identified with clear margin over #2</p>
              </div>
              <div className="p-3 bg-red-100 rounded text-center">
                <p className="font-semibold text-red-800 text-sm">No</p>
                <p className="text-xs">Wrong source identified with clear margin</p>
              </div>
              <div className="p-3 bg-amber-100 rounded text-center">
                <p className="font-semibold text-amber-800 text-sm">Inconclusive</p>
                <p className="text-xs">Top farms too close to determine (margin &lt; 5%)</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Section 12: Understanding Results */}
      <section id="understanding-results">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">12.</span>
              Understanding Results
            </CardTitle>
          </CardHeader>
          <CardContent className="prose prose-sm max-w-none space-y-4">
            <h4 className="font-semibold">Comparison Metrics</h4>

            <div className="overflow-x-auto">
              <table className="min-w-full text-sm border">
                <thead className="bg-muted">
                  <tr>
                    <th className="border p-2 text-left">Metric</th>
                    <th className="border p-2 text-left">What It Means</th>
                    <th className="border p-2 text-left">Why It Matters</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="border p-2 font-medium">Farms in Scope</td>
                    <td className="border p-2">Number of farms reached by any traceback path</td>
                    <td className="border p-2">More farms = more to investigate and potentially more product to recall</td>
                  </tr>
                  <tr className="bg-muted/50">
                    <td className="border p-2 font-medium">TLCs in Scope</td>
                    <td className="border p-2">Total unique lot codes analyzed</td>
                    <td className="border p-2">More TLCs = more records to review and analyze</td>
                  </tr>
                  <tr>
                    <td className="border p-2 font-medium">TLCS (Locations)</td>
                    <td className="border p-2">Unique locations (GLNs) where TLCs were created</td>
                    <td className="border p-2">More locations = wider geographic scope of investigation</td>
                  </tr>
                  <tr className="bg-muted/50">
                    <td className="border p-2 font-medium">Traceback Paths</td>
                    <td className="border p-2">Number of complete retail→farm paths traced</td>
                    <td className="border p-2">More paths = more supply chain routes to follow</td>
                  </tr>
                  <tr>
                    <td className="border p-2 font-medium">Investigation Time</td>
                    <td className="border p-2">Estimated calendar days to complete</td>
                    <td className="border p-2">Longer time = delayed recalls, more illnesses</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <h4 className="font-semibold mt-4">Expansion Factors</h4>
            <p className="text-sm">
              Expansion factors show how much larger the probabilistic investigation is compared to deterministic:
            </p>
            <ul className="text-sm list-disc list-inside">
              <li><strong>1.0x:</strong> No expansion (same scope)</li>
              <li><strong>2.0x:</strong> Twice as large</li>
              <li><strong>5.0x+:</strong> Significantly expanded (common for calculated lot codes)</li>
            </ul>

            <h4 className="font-semibold mt-4">Investigation Timing Breakdown</h4>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm mb-2">The timing estimate includes:</p>
              <ul className="text-sm list-disc list-inside space-y-1">
                <li><strong>Record Requests:</strong> Calendar time waiting for retailer responses (not parallelizable)</li>
                <li><strong>TLC Analysis:</strong> Person-hours reviewing lot code records</li>
                <li><strong>Traceback:</strong> Person-hours following supply chain links</li>
                <li><strong>Convergence Analysis:</strong> Person-hours analyzing patterns</li>
                <li><strong>Farm Verification:</strong> Person-hours verifying candidate farms</li>
              </ul>
              <p className="text-sm mt-2">
                <strong>Calendar days</strong> = Record request wait time + (Work hours ÷ Team capacity)
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Section 13: Examples */}
      <section id="examples">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">13.</span>
              Worked Examples
            </CardTitle>
          </CardHeader>
          <CardContent className="prose prose-sm max-w-none space-y-4">
            <h4 className="font-semibold">Example 1: Small Regional Outbreak</h4>
            <div className="p-4 bg-gray-50 rounded-lg mb-4">
              <p className="text-sm font-semibold mb-2">Configuration:</p>
              <ul className="text-sm list-disc list-inside mb-3">
                <li>5 farms, 2 packers, 3 DCs, 20 retailers</li>
                <li>7-day contamination, 90-day simulation</li>
                <li>70% interview success, 14-day record window</li>
              </ul>

              <p className="text-sm font-semibold mb-2">Typical Results:</p>
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="p-2 bg-green-100 rounded">
                  <p className="font-semibold text-green-800">Deterministic</p>
                  <ul className="list-disc list-inside">
                    <li>2-3 farms in scope</li>
                    <li>50-100 TLCs analyzed</li>
                    <li>~100 traceback paths</li>
                    <li>~4 days to complete</li>
                    <li>Source usually identified</li>
                  </ul>
                </div>
                <div className="p-2 bg-orange-100 rounded">
                  <p className="font-semibold text-orange-800">Probabilistic</p>
                  <ul className="list-disc list-inside">
                    <li>4-5 farms in scope</li>
                    <li>200-500 TLCs analyzed</li>
                    <li>~500 traceback paths</li>
                    <li>~6 days to complete</li>
                    <li>Source may be unclear</li>
                  </ul>
                </div>
              </div>

              <p className="text-sm mt-3">
                <strong>Interpretation:</strong> Even with a small network, calculated lot codes roughly
                double the investigation scope. The source farm is still usually identifiable through
                convergence, but with less certainty.
              </p>
            </div>

            <h4 className="font-semibold">Example 2: Large Network with Wide Date Window</h4>
            <div className="p-4 bg-gray-50 rounded-lg mb-4">
              <p className="text-sm font-semibold mb-2">Configuration:</p>
              <ul className="text-sm list-disc list-inside mb-3">
                <li>10 farms, 3 packers, 5 DCs, 50 retailers</li>
                <li>14-day contamination, 120-day simulation</li>
                <li>14-day date window at DCs</li>
              </ul>

              <p className="text-sm font-semibold mb-2">Typical Results:</p>
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="p-2 bg-green-100 rounded">
                  <p className="font-semibold text-green-800">Deterministic</p>
                  <ul className="list-disc list-inside">
                    <li>3-4 farms in scope</li>
                    <li>150-250 TLCs analyzed</li>
                    <li>~250 traceback paths</li>
                    <li>~5 days to complete</li>
                  </ul>
                </div>
                <div className="p-2 bg-orange-100 rounded">
                  <p className="font-semibold text-orange-800">Probabilistic</p>
                  <ul className="list-disc list-inside">
                    <li>8-10 farms in scope</li>
                    <li>1000-2000 TLCs analyzed</li>
                    <li>~2000 traceback paths</li>
                    <li>~10 days to complete</li>
                  </ul>
                </div>
              </div>

              <p className="text-sm mt-3">
                <strong>Interpretation:</strong> Wider date windows and longer contamination periods
                dramatically increase the scope expansion in probabilistic mode. The investigation
                takes twice as long and covers nearly all farms in the network.
              </p>
            </div>

            <h4 className="font-semibold">Example 3: Understanding Path Expansion</h4>
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm mb-2">Consider a single case at a retailer:</p>

              <div className="font-mono text-xs p-3 bg-white rounded border mb-3">
                <p className="mb-2"><strong>Deterministic path (1 path):</strong></p>
                <p>Retailer A → TLC-R001 → DC-West → TLC-D001 → Packer-X → TLC-P001 → Farm-1</p>

                <p className="mb-2 mt-4"><strong>Probabilistic paths (5 paths from same case):</strong></p>
                <p>Retailer A → TLC-R001 → DC-West claims TLC-D001 could be from:</p>
                <ul className="ml-4 list-disc list-inside">
                  <li>TLC-P001 (40% prob) → Farm-1</li>
                  <li>TLC-P002 (25% prob) → Farm-1</li>
                  <li>TLC-P003 (20% prob) → Farm-2</li>
                  <li>TLC-P004 (10% prob) → Farm-3</li>
                  <li>TLC-P005 (5% prob) → Farm-2</li>
                </ul>
              </div>

              <p className="text-sm">
                <strong>Result:</strong> One TLC at retail creates 5 traceback paths in probabilistic mode.
                With 50 TLCs to trace, that's 250 paths instead of 50 - a 5x expansion.
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Footer */}
      <div className="text-center text-sm text-muted-foreground pt-8 border-t">
        <p>FSMA 204 Outbreak Traceability Simulation</p>
        <p>For questions or feedback, contact the development team.</p>
      </div>
    </div>
  )
}
