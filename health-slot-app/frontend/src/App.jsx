// No login. The patient and clinic portals are separate views selected by the
// URL hash, so each can be opened on its own:
//   #patient  -> patient's phone
//   #clinic   -> clinic console
// A bare URL (no hash) defaults to the clinic console.

import { useEffect, useState } from 'react'
import PatientPortal from './screens/PatientPortal'
import ClinicPortal from './screens/ClinicPortal'

const roleFromHash = () => (window.location.hash.replace('#', '') === 'patient' ? 'patient' : 'clinic')

export default function App() {
  const [role, setRole] = useState(roleFromHash)

  useEffect(() => {
    const onHash = () => setRole(roleFromHash())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  return role === 'patient' ? <PatientPortal /> : <ClinicPortal />
}
