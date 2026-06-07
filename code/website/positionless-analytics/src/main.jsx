import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// This code was written by Claude in accordance with our course's AI use policy

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
)