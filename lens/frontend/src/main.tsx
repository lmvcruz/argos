import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// StrictMode is safe now - the logger uses batching + deduplication
// to prevent duplicate logs from reaching the backend
ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
