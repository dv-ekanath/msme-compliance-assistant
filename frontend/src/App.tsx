import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Alerts from './pages/Alerts'
import Checklist from './pages/Checklist'
import Copilot from './pages/Copilot'
import Dashboard from './pages/Dashboard'
import Filings from './pages/Filings'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Onboarding from './pages/Onboarding'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/dashboard/:businessId" element={<Dashboard />} />
        <Route path="/checklist/:businessId" element={<Checklist />} />
        <Route path="/copilot/:businessId" element={<Copilot />} />
        <Route path="/alerts/:businessId" element={<Alerts />} />
        <Route path="/filings/:businessId" element={<Filings />} />
        <Route path="/login" element={<Login />} />
      </Routes>
    </BrowserRouter>
  )
}
