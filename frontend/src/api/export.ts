const API_BASE_URL = '/api'

/**
 * Export simulation data to Excel file.
 * Triggers a file download in the browser.
 */
export async function exportSimulationToExcel(simulationId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/export/${simulationId}/excel`)

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(errorText || `Export failed with status ${response.status}`)
  }

  // Get filename from Content-Disposition header or generate default
  const contentDisposition = response.headers.get('Content-Disposition')
  let filename = `simulation_export_${simulationId.slice(0, 8)}.xlsx`

  if (contentDisposition) {
    const match = contentDisposition.match(/filename=(.+)/)
    if (match) {
      filename = match[1].replace(/["']/g, '')
    }
  }

  // Convert response to blob and trigger download
  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()

  // Cleanup
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

export const exportApi = {
  exportToExcel: exportSimulationToExcel,
}
