import { StrictMode, useState } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import LoginScreen from './components/LoginScreen'
import './styles.css'

// Show the login screen first, then the existing dashboard (App) once the user
// continues. App and all its data/logic are unchanged.
function Root() {
  const [entered, setEntered] = useState(false)
  if (!entered) return <LoginScreen onContinue={() => setEntered(true)} />
  return <App />
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Root />
  </StrictMode>,
)
