import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import logo from './images/GridIronGPT_Logo.png'

const API_BASE = (import.meta.env.VITE_API_BASE || 'http://localhost:8000')

export default function HomePage() {
  const navigate = useNavigate()
  const [healthError, setHealthError] = useState(null)

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(() => {})
      .catch(err => setHealthError(String(err)))
  }, [])

  return (
    <div className="app-shell landing-canvas">
      {healthError && <p className="hero-error">Health check failed: {healthError}</p>}

      <div className="landing-side landing-left">
        <div className="side-card">
          <span className="side-label">Start/Sit</span>
          <p>Smart lineup nudges with real weekly context.</p>
        </div>
        <div className="side-card">
          <span className="side-label">Roster Lens</span>
          <p>Instant roster insights.</p>
        </div>
        <div className="side-card">
          <span className="side-label">Matchups</span>
          <p>Weekly projections broken into position battles.</p>
        </div>
      </div>

      <main className="landing-center">
        <p className="hero-kicker">GridironGPT</p>
        <img
          className="landing-logo"
          src={logo}
          alt="GridIronGPT logo"
        />
        <h1>Fantasy Football, Supercharged</h1>
        <p className="hero-subtitle">
          The neon command center for start/sit decisions, roster edges, and league trends.
        </p>
        <button
          type="button"
          className="cta-button animated"
          onClick={() => navigate('/app')}
        >
          Get started
        </button>
      </main>

      <div className="landing-side landing-right">
        <div className="side-card">
          <span className="side-label">Top 10</span>
          <p>Leaders through the most recent completed week.</p>
        </div>
        <div className="side-card">
          <span className="side-label">League Intel</span>
          <p>Strengths, weaknesses, and roster trends.</p>
        </div>
        <div className="side-card">
          <span className="side-label">Live Sync</span>
          <p>Fresh data pulls before every analysis.</p>
        </div>
      </div>
    </div>
  )
}
