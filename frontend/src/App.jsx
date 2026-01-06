import { useEffect, useMemo, useState } from 'react'
import './App.css'

const API_BASE = (import.meta.env.VITE_API_BASE || 'http://localhost:8000')

const STARTER_HINTS = [
  'compare Alice vs Bob week 7',
  'compare Micah versus Jax week 12 include bench',
  'compare my team vs Sam week 9'
]

function parseComparePrompt(input) {
  const text = input.trim()
  const weekMatch = text.match(/week\s+(\d{1,2})/i)
  const week = weekMatch ? Number(weekMatch[1]) : null
  const includeBench = /include\s+bench|bench/i.test(text)

  const compareMatch = text.match(/compare\s+(.+?)\s+(?:vs|versus|and)\s+(.+?)(?:\s+week|\s*$)/i)
  if (!compareMatch || !week) {
    return { error: 'Try "compare Alice vs Bob week 7".' }
  }

  const userA = compareMatch[1].trim()
  const userB = compareMatch[2].trim()
  if (!userA || !userB) {
    return { error: 'I need two roster names to compare.' }
  }

  return { userA, userB, week, includeBench }
}

export default function App() {
  const [health, setHealth] = useState(null)
  const [healthError, setHealthError] = useState(null)
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Ask me to compare two rosters. I will pull projections and summarize the edge.'
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const apiLabel = useMemo(() => API_BASE.replace(/^https?:\/\//, ''), [])

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(r => r.json())
      .then(setHealth)
      .catch(err => setHealthError(String(err)))
  }, [])

  async function handleSubmit(event) {
    event.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = { role: 'user', content: input.trim() }
    setMessages(prev => [...prev, userMessage])
    setInput('')

    const parsed = parseComparePrompt(userMessage.content)
    if (parsed.error) {
      setMessages(prev => [...prev, { role: 'system', content: parsed.error }])
      return
    }

    const payload = {
      user_a: parsed.userA,
      user_b: parsed.userB,
      week: parsed.week,
      include_bench: parsed.includeBench
    }

    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/ai/compare-rosters`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        const errText = await response.text()
        throw new Error(errText || 'Request failed')
      }

      const data = await response.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.summary }])
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { role: 'system', content: `Error: ${err.message || String(err)}` }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero-title">
          <p className="hero-kicker">GridironGPT</p>
          <h1>Roster comparison command center</h1>
          <p className="hero-subtitle">
            Type a matchup request, we will call your AI service layer and return a clear edge.
          </p>
        </div>
        <div className="hero-status">
          <span className={`pill ${health ? 'pill-online' : 'pill-offline'}`}>
            {health ? 'API online' : 'API offline'}
          </span>
          <span className="pill pill-quiet">{apiLabel}</span>
        </div>
        {healthError && <p className="hero-error">Health check failed: {healthError}</p>}
      </header>

      <main className="chat-card">
        <div className="chat-header">
          <h2>Live roster chat</h2>
          <p>Compare two owners by name and week.</p>
        </div>

        <div className="chat-body">
          {messages.map((msg, index) => (
            <div key={`${msg.role}-${index}`} className={`chat-message ${msg.role}`}>
              <span className="chat-role">{msg.role}</span>
              <p>{msg.content}</p>
            </div>
          ))}
          {isLoading && (
            <div className="chat-message assistant loading">
              <span className="chat-role">assistant</span>
              <p>Crunching projections and lineup edges...</p>
            </div>
          )}
        </div>

        <form className="chat-input" onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={event => setInput(event.target.value)}
            placeholder="compare Alice vs Bob week 7"
          />
          <button type="submit" disabled={isLoading}>
            Compare
          </button>
        </form>

        <div className="chat-hints">
          {STARTER_HINTS.map(hint => (
            <button key={hint} type="button" onClick={() => setInput(hint)}>
              {hint}
            </button>
          ))}
        </div>
      </main>
    </div>
  )
}
