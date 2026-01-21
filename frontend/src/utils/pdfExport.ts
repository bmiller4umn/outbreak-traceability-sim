import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'
import html2canvas from 'html2canvas'
import type { MonteCarloResult } from '@/api/types'

// Extend jsPDF type to include autoTable
declare module 'jspdf' {
  interface jsPDF {
    lastAutoTable: { finalY: number }
  }
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

function addSection(doc: jsPDF, title: string, y: number): number {
  doc.setFontSize(14)
  doc.setFont('helvetica', 'bold')
  doc.text(title, 14, y)
  return y + 8
}

export async function generateMonteCarloReport(
  result: MonteCarloResult,
  chartsContainerRef?: HTMLElement | null
): Promise<void> {
  const doc = new jsPDF()
  const config = result.config
  const pageWidth = doc.internal.pageSize.width
  let y = 20

  // Title
  doc.setFontSize(20)
  doc.setFont('helvetica', 'bold')
  doc.text('Monte Carlo Simulation Report', 14, y)
  y += 10

  // Subtitle with date
  doc.setFontSize(10)
  doc.setFont('helvetica', 'normal')
  doc.setTextColor(100)
  doc.text(`Generated: ${new Date().toLocaleString()}`, 14, y)
  doc.text(`Iterations Completed: ${result.iterationsCompleted}`, 14, y + 5)
  doc.setTextColor(0)
  y += 15

  // Configuration Section
  y = addSection(doc, '1. Simulation Configuration', y)

  autoTable(doc, {
    startY: y,
    head: [['Parameter', 'Value', 'Parameter', 'Value']],
    body: [
      ['Farms', config.numFarms.toString(), 'Retailers', config.numRetailers.toString()],
      ['Packers', config.numPackers.toString(), 'Distribution Centers', config.numDistributionCenters.toString()],
      ['Contamination Rate', formatPercent(config.contaminationRate), 'Contamination Duration', `${config.contaminationDurationDays} days`],
      ['Interview Success Rate', `${config.interviewSuccessRate}%`, 'Record Collection Window', `${config.recordCollectionWindowDays} days`],
      ['Lot Code Strategy', config.inventoryStrategy, 'Date Window', `${config.dateWindowDays} days`],
      ['Simulation Duration', `${config.simulationDays} days`, 'Pathogen', config.pathogen],
      ['Monte Carlo Iterations', config.numIterations.toString(), 'Random Seed', config.baseRandomSeed?.toString() ?? 'Random'],
    ],
    theme: 'striped',
    headStyles: { fillColor: [59, 130, 246], fontSize: 9 },
    bodyStyles: { fontSize: 9 },
    margin: { left: 14, right: 14 },
    columnStyles: {
      0: { fontStyle: 'bold', cellWidth: 45 },
      1: { cellWidth: 40 },
      2: { fontStyle: 'bold', cellWidth: 50 },
      3: { cellWidth: 40 },
    },
  })
  y = doc.lastAutoTable.finalY + 12

  // Source Identification Results
  y = addSection(doc, '2. Source Identification Outcomes', y)

  autoTable(doc, {
    startY: y,
    head: [['Outcome', 'Deterministic', 'Probabilistic', 'Difference']],
    body: [
      [
        'Correct (Yes)',
        formatPercent(result.deterministicIdentification.yesRate),
        formatPercent(result.probabilisticIdentification.yesRate),
        formatPercent(result.deterministicIdentification.yesRate - result.probabilisticIdentification.yesRate),
      ],
      [
        'Inconclusive',
        formatPercent(result.deterministicIdentification.inconclusiveRate),
        formatPercent(result.probabilisticIdentification.inconclusiveRate),
        formatPercent(result.deterministicIdentification.inconclusiveRate - result.probabilisticIdentification.inconclusiveRate),
      ],
      [
        'Incorrect (No)',
        formatPercent(result.deterministicIdentification.noRate),
        formatPercent(result.probabilisticIdentification.noRate),
        formatPercent(result.deterministicIdentification.noRate - result.probabilisticIdentification.noRate),
      ],
      [
        'Mean Source Rank',
        result.deterministicIdentification.meanRank.toFixed(1),
        result.probabilisticIdentification.meanRank.toFixed(1),
        (result.deterministicIdentification.meanRank - result.probabilisticIdentification.meanRank).toFixed(1),
      ],
    ],
    theme: 'striped',
    headStyles: { fillColor: [34, 197, 94] },
    margin: { left: 14, right: 14 },
  })
  y = doc.lastAutoTable.finalY + 8

  // Statistical Significance
  if (result.identificationPValue !== null) {
    doc.setFontSize(10)
    doc.setFont('helvetica', 'normal')
    const significant = result.identificationDifferenceSignificant
    doc.text(
      `McNemar's Test: p-value = ${result.identificationPValue.toFixed(4)} (${significant ? 'Statistically Significant' : 'Not Significant'} at α=0.05)`,
      14,
      y
    )
    y += 10
  }

  // Expansion Metrics Table
  y = addSection(doc, '3. Investigation Scope Expansion', y)

  autoTable(doc, {
    startY: y,
    head: [['Metric', 'Mean', 'Std Dev', 'Min', 'Median', 'Max', '95% Range']],
    body: [
      [
        'Farm Scope Expansion',
        `${result.farmScopeExpansion.mean.toFixed(2)}x`,
        result.farmScopeExpansion.std.toFixed(2),
        `${result.farmScopeExpansion.min.toFixed(2)}x`,
        `${result.farmScopeExpansion.median.toFixed(2)}x`,
        `${result.farmScopeExpansion.max.toFixed(2)}x`,
        `[${result.farmScopeExpansion.p5.toFixed(2)}, ${result.farmScopeExpansion.p95.toFixed(2)}]`,
      ],
      [
        'TLC Scope Expansion',
        `${result.tlcScopeExpansion.mean.toFixed(2)}x`,
        result.tlcScopeExpansion.std.toFixed(2),
        `${result.tlcScopeExpansion.min.toFixed(2)}x`,
        `${result.tlcScopeExpansion.median.toFixed(2)}x`,
        `${result.tlcScopeExpansion.max.toFixed(2)}x`,
        `[${result.tlcScopeExpansion.p5.toFixed(2)}, ${result.tlcScopeExpansion.p95.toFixed(2)}]`,
      ],
      [
        'TLCS Expansion',
        `${result.tlcsLocationExpansion.mean.toFixed(2)}x`,
        result.tlcsLocationExpansion.std.toFixed(2),
        `${result.tlcsLocationExpansion.min.toFixed(2)}x`,
        `${result.tlcsLocationExpansion.median.toFixed(2)}x`,
        `${result.tlcsLocationExpansion.max.toFixed(2)}x`,
        `[${result.tlcsLocationExpansion.p5.toFixed(2)}, ${result.tlcsLocationExpansion.p95.toFixed(2)}]`,
      ],
      [
        'Path Expansion',
        `${result.pathExpansion.mean.toFixed(2)}x`,
        result.pathExpansion.std.toFixed(2),
        `${result.pathExpansion.min.toFixed(2)}x`,
        `${result.pathExpansion.median.toFixed(2)}x`,
        `${result.pathExpansion.max.toFixed(2)}x`,
        `[${result.pathExpansion.p5.toFixed(2)}, ${result.pathExpansion.p95.toFixed(2)}]`,
      ],
    ],
    theme: 'striped',
    headStyles: { fillColor: [249, 115, 22], fontSize: 8 },
    bodyStyles: { fontSize: 8 },
    margin: { left: 14, right: 14 },
  })
  y = doc.lastAutoTable.finalY + 8

  // 95% CI note
  doc.setFontSize(9)
  doc.text(
    `95% Confidence Interval for Mean Farm Expansion: [${result.meanExpansion95CI[0].toFixed(2)}, ${result.meanExpansion95CI[1].toFixed(2)}]`,
    14,
    y
  )
  y += 10

  // Absolute Scope Metrics
  y = addSection(doc, '4. Absolute Scope Metrics', y)

  autoTable(doc, {
    startY: y,
    head: [['Metric', 'Deterministic (Mean)', 'Probabilistic (Mean)']],
    body: [
      [
        'Farms in Scope',
        result.detFarmsInScope.mean.toFixed(1),
        result.probFarmsInScope.mean.toFixed(1),
      ],
      [
        'TLCs in Scope',
        result.detTlcsInScope.mean.toFixed(1),
        result.probTlcsInScope.mean.toFixed(1),
      ],
      [
        'TLC Sources (TLCS) in Scope',
        result.detTlcsLocations.mean.toFixed(1),
        result.probTlcsLocations.mean.toFixed(1),
      ],
    ],
    theme: 'striped',
    headStyles: { fillColor: [139, 92, 246] },
    margin: { left: 14, right: 14 },
  })
  y = doc.lastAutoTable.finalY + 10

  // Case Statistics
  y = addSection(doc, '5. Case Statistics', y)

  autoTable(doc, {
    startY: y,
    head: [['Statistic', 'Value']],
    body: [
      ['Mean Cases per Simulation', result.totalCases.mean.toFixed(1)],
      ['Std Dev', result.totalCases.std.toFixed(1)],
      ['Min', result.totalCases.min.toFixed(0)],
      ['Median', result.totalCases.median.toFixed(0)],
      ['Max', result.totalCases.max.toFixed(0)],
    ],
    theme: 'striped',
    headStyles: { fillColor: [59, 130, 246] },
    margin: { left: 14, right: 14 },
    tableWidth: 100,
  })

  // Capture charts if container is provided
  if (chartsContainerRef) {
    doc.addPage()
    y = 20

    doc.setFontSize(16)
    doc.setFont('helvetica', 'bold')
    doc.text('6. Visual Results', 14, y)
    y += 10

    doc.setFontSize(10)
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(100)
    doc.text('Charts captured from the Monte Carlo Results dashboard:', 14, y)
    doc.setTextColor(0)
    y += 10

    try {
      // Capture the charts container as an image
      const canvas = await html2canvas(chartsContainerRef, {
        scale: 2, // Higher resolution
        backgroundColor: '#ffffff',
        logging: false,
        useCORS: true,
      })

      const imgData = canvas.toDataURL('image/png')

      // Calculate dimensions to fit the page
      const imgWidth = pageWidth - 28 // margins
      const imgHeight = (canvas.height * imgWidth) / canvas.width

      // Check if we need multiple pages for the image
      const pageHeight = doc.internal.pageSize.height - 30 // leave margin

      if (imgHeight <= pageHeight - y) {
        // Fits on current page
        doc.addImage(imgData, 'PNG', 14, y, imgWidth, imgHeight)
      } else {
        // Need to split across pages
        let remainingHeight = imgHeight
        let sourceY = 0

        while (remainingHeight > 0) {
          const availableHeight = doc.internal.pageSize.height - y - 15
          const sliceHeight = Math.min(availableHeight, remainingHeight)
          const sliceRatio = sliceHeight / imgHeight

          // Create a temporary canvas for this slice
          const sliceCanvas = document.createElement('canvas')
          sliceCanvas.width = canvas.width
          sliceCanvas.height = canvas.height * sliceRatio
          const ctx = sliceCanvas.getContext('2d')

          if (ctx) {
            ctx.drawImage(
              canvas,
              0, sourceY * (canvas.height / imgHeight),
              canvas.width, sliceCanvas.height,
              0, 0,
              sliceCanvas.width, sliceCanvas.height
            )

            const sliceData = sliceCanvas.toDataURL('image/png')
            doc.addImage(sliceData, 'PNG', 14, y, imgWidth, sliceHeight)
          }

          remainingHeight -= sliceHeight
          sourceY += sliceHeight

          if (remainingHeight > 0) {
            doc.addPage()
            y = 20
          }
        }
      }
    } catch (error) {
      console.error('Failed to capture charts:', error)
      doc.setFontSize(10)
      doc.text('(Charts could not be captured)', 14, y)
    }
  }

  // Key Findings on final page
  doc.addPage()
  y = 20

  y = addSection(doc, '7. Key Findings', y)

  doc.setFontSize(11)
  doc.setFont('helvetica', 'normal')

  const findings = [
    `1. Source Identification: With full lot code compliance (deterministic tracking), the contamination source was correctly identified in ${formatPercent(result.deterministicIdentification.yesRate)} of simulations. With calculated lot codes (probabilistic), correct identification dropped to ${formatPercent(result.probabilisticIdentification.yesRate)}.`,
    '',
    `2. Investigation Scope Impact: When distribution centers use calculated lot codes instead of exact TLC tracking, the investigation scope expands by an average of ${result.farmScopeExpansion.mean.toFixed(2)}x for farms and ${result.tlcScopeExpansion.mean.toFixed(2)}x for TLCs.`,
    '',
    `3. Practical Implications: This scope expansion means investigators must examine approximately ${result.probFarmsInScope.mean.toFixed(1)} farms on average with calculated lot codes, compared to ${result.detFarmsInScope.mean.toFixed(1)} farms with full compliance - potentially leading to larger recalls and more wasted product.`,
    '',
    `4. Statistical Confidence: Based on ${result.iterationsCompleted} simulation iterations, the 95% confidence interval for mean farm scope expansion is [${result.meanExpansion95CI[0].toFixed(2)}, ${result.meanExpansion95CI[1].toFixed(2)}].`,
  ]

  let textY = y
  findings.forEach((finding) => {
    if (finding === '') {
      textY += 4
    } else {
      const lines = doc.splitTextToSize(finding, pageWidth - 28)
      doc.text(lines, 14, textY)
      textY += lines.length * 5 + 2
    }
  })

  // Footer on all pages
  const pageCount = doc.getNumberOfPages()
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i)
    doc.setFontSize(8)
    doc.setTextColor(128)
    doc.text(
      `Page ${i} of ${pageCount} | Outbreak Traceability Simulation - Monte Carlo Report`,
      pageWidth / 2,
      doc.internal.pageSize.height - 10,
      { align: 'center' }
    )
  }

  // Save the PDF
  const timestamp = new Date().toISOString().slice(0, 10)
  doc.save(`monte-carlo-report-${timestamp}.pdf`)
}
