// Flow: login screen -> pick a role -> the matching portal.
//   (no role / #login) -> LoginScreen
//   #patient           -> patient's phone
//   #clinic            -> clinic console
// The choice is kept in the URL hash so a refresh stays put, and each portal can
// still be linked to directly.

import { useEffect, useState } from 'react'
import LoginScreen from './components/LoginScreen'
import PatientPortal from './screens/PatientPortal'
import ClinicPortal from './screens/ClinicPortal'

const roleFromHash = () => {
  const h = window.location.hash.replace('#', '')
  return h === 'patient' || h === 'clinic' ? h : null
}

export default function App() {
  const [role, setRole] = useState(roleFromHash)

  useEffect(() => {
    const onHash = () => setRole(roleFromHash())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  const enter = (r) => {
    window.location.hash = r
    setRole(r)
  }

  if (role === 'patient') return <PatientPortal />
  if (role === 'clinic') return <ClinicPortal />
  return <LoginScreen onEnter={enter} />
}
