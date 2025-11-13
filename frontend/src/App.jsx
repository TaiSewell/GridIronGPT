import { useEffect, useState } from 'react'

const API_BASE = (import.meta.env.VITE_API_BASE || 'http://localhost:8000');

export default function App() {
  const [health, setHealth] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(r => r.json())
      .then(setHealth)
      .catch(err => setError(String(err)))
  }, [])

  return (
    <div className="min-h-screen p-6">
      <header className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold">GridironGPT</h1>
        <p className="text-sm text-gray-600">Phase 0 – Bootstrap</p>
      </header>

      <main className="max-w-3xl mx-auto mt-6">
        <div className="rounded-xl border p-4 bg-white shadow-sm">
          <h2 className="font-semibold mb-2">Backend Health</h2>
          {!health && !error && <p>Checking...</p>}
          {error && <p className="text-red-600">Error: {error}</p>}
          {health && (
            <pre className="text-sm bg-gray-50 p-3 rounded-lg overflow-auto">
{JSON.stringify(health, null, 2)}
            </pre>
          )}
          <p className="text-xs text-gray-500 mt-2">
            API Base: <code>{API_BASE}</code>
          </p>
        </div>
      </main>
    </div>
  )
}