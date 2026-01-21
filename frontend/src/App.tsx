import { Routes, Route } from 'react-router-dom'
import MainLayout from './components/layout/MainLayout'
import SimulationPage from './pages/SimulationPage'
import ComparisonPage from './pages/ComparisonPage'
import InvestigationPage from './pages/InvestigationPage'
import MonteCarloPage from './pages/MonteCarloPage'
import UserGuidePage from './pages/UserGuidePage'
import AboutPage from './pages/AboutPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<SimulationPage />} />
        <Route path="compare" element={<ComparisonPage />} />
        <Route path="investigate" element={<InvestigationPage />} />
        <Route path="monte-carlo" element={<MonteCarloPage />} />
        <Route path="guide" element={<UserGuidePage />} />
        <Route path="about" element={<AboutPage />} />
      </Route>
    </Routes>
  )
}

export default App
