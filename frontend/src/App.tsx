import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Checklist from './pages/Checklist'
import Dashboard from './pages/Dashboard'
import Landing from './pages/Landing'
import Onboarding from './pages/Onboarding'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/dashboard/:businessId" element={<Dashboard />} />
        <Route path="/checklist/:businessId" element={<Checklist />} />
      </Routes>
    </BrowserRouter>
  )
}
