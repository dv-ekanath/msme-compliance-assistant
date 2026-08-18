import { Navigate } from 'react-router-dom'

export default function Landing() {
  const lastBusinessId = localStorage.getItem('lastBusinessId')
  return <Navigate to={lastBusinessId ? `/dashboard/${lastBusinessId}` : '/onboarding'} replace />
}
