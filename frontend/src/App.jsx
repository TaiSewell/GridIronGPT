import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './App.css'
import logo from "./images/GridIronGPT_Logo.png";

const API_BASE = (import.meta.env.VITE_API_BASE || 'http://localhost:8000')

const STARTER_HINTS = [
  'compare Etac vs JDose week 10',
  'compare Tai versus JDOse week 12 include bench',
  'compare my team vs Etac week 9',
  'who should I start this week 7',
  'give me insights on my roster',
  'give me the top 10 players this year',
  'give me your thoughts overall on the league this year',
]

const LOCAL_TEAM_KEY = 'gridiron.myTeam'

function loadStoredTeam() {
  let result = null
  try {
    const raw = localStorage.getItem(LOCAL_TEAM_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      if (parsed?.ownerId && parsed?.displayName) {
        result = parsed
      }
    }
  } catch {
    result = null
  }
  return result
}

function storeTeamSelection(team) {
  let success = false
  try {
    localStorage.setItem(LOCAL_TEAM_KEY, JSON.stringify(team))
    success = true
  } catch {
    success = false
  }
  return success
}

function resolveMyTeamText(text, myTeam) {
  const result = { text, needsTeam: false }
  if (/\bmy team\b/i.test(text)) {
    if (myTeam?.displayName) {
      result.text = text.replace(/my team/gi, myTeam.displayName)
    } else {
      result.needsTeam = true
    }
  }
  return result
}

function parseFantasyLeadersPrompt(input) {
  const text = input.trim()
  const result = { intent: false }
  const limitMatch = text.match(/top\s+(\d{1,3})\s*players/i)
  const hasYear = /this\s+year/i.test(text)

  if (limitMatch && hasYear) {
    const limitValue = Number(limitMatch[1])
    result.intent = true
    if (!limitValue || Number.isNaN(limitValue)) {
      result.error = 'Missing number. Try: `give me the top 10 players this year`.'
    } else if (limitValue < 1 || limitValue > 100) {
      result.error = 'Number out of range. Try: `give me the top 10 players this year`.'
    } else {
      result.limit = limitValue
    }
  }

  return result
}

function parseLeagueSummaryPrompt(input) {
  const text = input.trim()
  const result = { intent: false }
  const hasLeague = /league/i.test(text)
  const hasThoughts = /thoughts|overview|summary/i.test(text)
  const hasYear = /this\s+year/i.test(text)

  if (hasLeague && hasThoughts && hasYear) {
    result.intent = true
  }

  return result
}

function parseComparePrompt(input) {
  const text = input.trim()
  const weekMatch = text.match(/week\s+(\d{1,2})/i)
  const week = weekMatch ? Number(weekMatch[1]) : null
  const includeBench = /include\s+bench|bench/i.test(text)

  const compareMatch = text.match(/compare\s+(.+?)\s+(?:vs|versus|and)\s+(.+?)(?:\s+week|\s*$)/i)
  if (!compareMatch || !week) {
    if (!week) {
      return { error: 'Missing week. Try: `compare Alice vs Bob week 7`.' }
    }
    return { error: 'Missing roster names. Try: `compare Alice vs Bob week 7`.' }
  }

  const userA = compareMatch[1].trim()
  const userB = compareMatch[2].trim()
  if (!userA || !userB) {
    return { error: 'Missing roster names. Try: `compare Alice vs Bob week 7`.' }
  }

  return { userA, userB, week, includeBench }
}

function parseStartSitPrompt(input) {
  const text = input.trim()
  const result = { intent: false }
  const isStartSit = /(start\s+sit|start\s+or\s+sit|who\s+should\s+i\s+start|should\s+i\s+bench|bench\s+or\s+start|roster\s+recommendations|lineup\s+recommendations)/i.test(text)
  if (isStartSit) {
    const weekMatch = text.match(/week\s+(\d{1,2})/i)
    const week = weekMatch ? Number(weekMatch[1]) : null
    const userMatch = text.match(/for\s+(.+?)(?:\s+week|\s*$)/i)
    const userA = userMatch ? userMatch[1].trim() : ''

    result.intent = true
    result.week = week
    if (!week) {
      result.error = 'Missing week. Try: `who should I start week 7`.'
    } else if (!userA) {
      result.useMyTeam = true
    } else {
      result.userA = userA
      result.week = week
    }
  }
  return result
}

function parseRosterInsightsPrompt(input) {
  const text = input.trim()
  const result = { intent: false }
  const isInsights = /(roster\s+insights|insights\s+on\s+my\s+roster|insights\s+on\s+roster|team\s+insights|roster\s+breakdown|my\s+roster\s+insights)/i.test(text)
  if (isInsights) {
    const userMatch = text.match(/for\s+(.+?)(?:\s+week|\s*$)/i)
    const userA = userMatch ? userMatch[1].trim() : ''
    const useMyTeam = /\bmy\s+roster\b|\bmy\s+team\b/i.test(text)

    result.intent = true
    if (userA) {
      result.userA = userA
    } else if (useMyTeam) {
      result.useMyTeam = true
    } else {
      result.error = 'Missing roster name. Try: `give me insights on my roster`.'
    }
  }
  return result
}

export default function App() {
  const navigate = useNavigate()
  const [healthError, setHealthError] = useState(null)
  const [myTeam, setMyTeam] = useState(() => loadStoredTeam())
  const [teamOptions, setTeamOptions] = useState([])
  const [pendingInput, setPendingInput] = useState('')
  const [adminLeagueId, setAdminLeagueId] = useState('')
  const [adminStatus, setAdminStatus] = useState('')
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Ask me questions based on your fantasy league. I will do my best to assist you!'
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(() => {})
      .catch(err => setHealthError(String(err)))
  }, [])

  useEffect(() => {
    if (!myTeam && teamOptions.length === 0) {
      fetchTeamOptions().then(options => setTeamOptions(options))
    }
  }, [myTeam, teamOptions.length])

  async function fetchTeamOptions() {
    let options = []
    try {
      const [rostersResponse, usersResponse] = await Promise.all([
        fetch(`${API_BASE}/rosters/league`),
        fetch(`${API_BASE}/users`)
      ])

      if (!rostersResponse.ok || !usersResponse.ok) {
        throw new Error('Failed to load roster owners.')
      }

      const rosters = await rostersResponse.json()
      const users = await usersResponse.json()
      const userMap = {}
      users.forEach(user => {
        userMap[user.user_id] = user
      })

      options = rosters
        .filter(roster => roster.owner_id)
        .map(roster => {
          const user = userMap[roster.owner_id] || {}
          return {
            ownerId: roster.owner_id,
            displayName: user.display_name || user.team_name || roster.owner_id,
            teamName: user.team_name || ''
          }
        })
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { role: 'system', content: `Error: ${err.message || String(err)}` }
      ])
    }
    return options
  }

  async function handleLeagueSwitch(event) {
    event.preventDefault()
    const trimmedLeagueId = adminLeagueId.trim()
    if (!trimmedLeagueId) {
      setAdminStatus('Missing league id. Try: `1266923357840871424`.')
      return
    }

    const confirmSwitch = window.confirm(
      `Switch active league to ${trimmedLeagueId}? This will refresh league data.`
    )
    if (!confirmSwitch) {
      setAdminStatus('League switch canceled.')
      return
    }

    setAdminStatus('Switching league and syncing...')
    try {
      const response = await fetch(`${API_BASE}/admin/league`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ league_id: trimmedLeagueId })
      })

      if (!response.ok) {
        const errText = await response.text()
        throw new Error(errText || 'Request failed')
      }

      localStorage.removeItem(LOCAL_TEAM_KEY)
      setMyTeam(null)
      setTeamOptions([])
      const options = await fetchTeamOptions()
      setTeamOptions(options)
      setAdminStatus(`Active league switched to ${trimmedLeagueId}.`)
    } catch (err) {
      setAdminStatus(`Error: ${err.message || String(err)}`)
    }
  }

  function handleTeamSelect(team) {
    const saved = storeTeamSelection(team)
    if (saved) {
      setMyTeam(team)
      setTeamOptions([])
      setMessages(prev => [
        ...prev,
        { role: 'system', content: `Saved your team as ${team.displayName}.` }
      ])
      if (pendingInput) {
        setInput(pendingInput)
        setPendingInput('')
      }
    } else {
      setMessages(prev => [
        ...prev,
        { role: 'system', content: 'Unable to store your team selection.' }
      ])
    }
  }

  function handleTeamReset() {
    try {
      localStorage.removeItem(LOCAL_TEAM_KEY)
    } catch (err) {
      // Ignore storage errors
    }
    setMyTeam(null)
    setTeamOptions([])
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!input.trim() || isLoading) return

    const rawText = input.trim()
    const resolvedText = resolveMyTeamText(rawText, myTeam)
    const userMessage = { role: 'user', content: rawText }
    setMessages(prev => [...prev, userMessage])
    setInput('')

    if (resolvedText.needsTeam) {
      setPendingInput(rawText)
      setMessages(prev => [
        ...prev,
        { role: 'system', content: 'Select your team to use "my team" prompts.' }
      ])
      if (!teamOptions.length) {
        const options = await fetchTeamOptions()
        setTeamOptions(options)
      }
      return
    }

    const inputText = resolvedText.text
    const leagueParsed = parseLeagueSummaryPrompt(inputText)
    const fantasyParsed = parseFantasyLeadersPrompt(inputText)
    if (leagueParsed.intent && fantasyParsed.intent) {
      setMessages(prev => [
        ...prev,
        { role: 'system', content: 'Too many requests. Try: `give me the top 10 players this year`.' }
      ])
      return
    }

    if (leagueParsed.intent) {
      setIsLoading(true)
      try {
        const response = await fetch(`${API_BASE}/ai/league-summary`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({})
        })

        if (!response.ok) {
          const errText = await response.text()
          throw new Error(errText || 'Request failed')
        }

        const data = await response.json()
        const formatted = [data.summary, data.details].filter(Boolean).join('\n\n')
        setMessages(prev => [
          ...prev,
          { role: 'assistant', content: formatted }
        ])
      } catch (err) {
        setMessages(prev => [
          ...prev,
          { role: 'system', content: `Error: ${err.message || String(err)}` }
        ])
      } finally {
        setIsLoading(false)
      }
      return
    }

    if (fantasyParsed.intent && fantasyParsed.error) {
      setMessages(prev => [...prev, { role: 'system', content: fantasyParsed.error }])
      return
    }

    const rosterInsightsParsed = fantasyParsed.intent
      ? { intent: false }
      : parseRosterInsightsPrompt(inputText)
    if (rosterInsightsParsed.intent && rosterInsightsParsed.useMyTeam) {
      if (myTeam?.displayName) {
        rosterInsightsParsed.userA = myTeam.displayName
      } else {
        setMessages(prev => [
          ...prev,
          { role: 'system', content: 'Missing roster name. Try: `give me insights on my roster`.' }
        ])
        return
      }
    } else if (rosterInsightsParsed.intent && rosterInsightsParsed.error) {
      setMessages(prev => [...prev, { role: 'system', content: rosterInsightsParsed.error }])
      return
    }

    const startSitParsed = fantasyParsed.intent
      ? { intent: false }
      : parseStartSitPrompt(inputText)
    if (startSitParsed.intent && startSitParsed.useMyTeam) {
      if (myTeam?.displayName) {
        startSitParsed.userA = myTeam.displayName
      } else {
        setMessages(prev => [
          ...prev,
          { role: 'system', content: 'Missing roster name. Try: `who should I start week 7`.' }
        ])
        return
      }
    } else if (startSitParsed.intent && startSitParsed.error) {
      setMessages(prev => [...prev, { role: 'system', content: startSitParsed.error }])
      return
    }

    const parsed = fantasyParsed.intent || startSitParsed.intent || rosterInsightsParsed.intent
      ? null
      : parseComparePrompt(inputText)
    if (parsed?.error) {
      setMessages(prev => [...prev, { role: 'system', content: parsed.error }])
      return
    }

    const payload = fantasyParsed.intent
      ? {
          limit: fantasyParsed.limit
        }
      : rosterInsightsParsed.intent
        ? {
            user_a: rosterInsightsParsed.userA
          }
        : startSitParsed.intent
        ? {
            user_a: startSitParsed.userA,
            week: startSitParsed.week
          }
        : {
            user_a: parsed.userA,
            user_b: parsed.userB,
            week: parsed.week,
            include_bench: parsed.includeBench
          }

    setIsLoading(true)
    try {
      const endpoint = fantasyParsed.intent
        ? 'fantasy-leaders'
        : rosterInsightsParsed.intent
          ? 'roster-insights'
          : startSitParsed.intent
          ? 'start-sit'
          : 'compare-rosters'
      const response = await fetch(`${API_BASE}/ai/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        const errText = await response.text()
        throw new Error(errText || 'Request failed')
      }

      const data = await response.json()
      let formatted = ''
      if (fantasyParsed.intent) {
        formatted = [data.summary, data.details].filter(Boolean).join('\n\n')
      } else if (rosterInsightsParsed.intent) {
        formatted = [data.summary, data.details].filter(Boolean).join('\n\n')
      } else if (startSitParsed.intent) {
        formatted = [data.recommendation, data.reasoning].filter(Boolean).join('\n\n')
      } else {
        const rawReasoning = data.reasoning || ''
        const trimmedReasoning = rawReasoning.replace(/^Positional edges:\s*/i, '')
        const reasoningItems = trimmedReasoning
          ? trimmedReasoning.split(',').map(chunk => ` - ${chunk.trim()}`)
          : [' - Projections are close across positions.']

        const recommendationLine = data.recommendation
          ? `Recommendation to your lineup: ${data.recommendation.replace(/^Recommendation to your lineup:\s*/i, '')}`
          : 'Recommendation to your lineup: no changes suggested.'

        formatted = [
          data.summary,
          '',
          'Positional edges: ',
          ...reasoningItems,
          '',
          recommendationLine
        ].join('\n')
      }
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: formatted }
      ])
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { role: 'system', content: `Error: ${err.message || String(err)}` }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  if (!myTeam) {
    return (
      <div className="app-shell">
        <header className="hero welcome-hero">
          <div className="hero-title">
            <p className="hero-kicker">GridironGPT</p>
            <h1>Roster Selection</h1>
            <p className="hero-subtitle">
              Select your team to personalize your league insights and unlock your chat.
            </p>
            <button type="button" className="home-button" onClick={() => navigate('/')}>
              Home
            </button>
          </div>
          <img
            className="welcome-logo"
            src={logo}
            alt="GridironGPT logo"
          />
          {healthError && <p className="hero-error">Health check failed: {healthError}</p>}
        </header>

        <section className="admin-panel">
          <div className="admin-header">
            <h2>League ID</h2>
            <p>Switch the active league id and refresh data.</p>
          </div>
          <form className="admin-form" onSubmit={handleLeagueSwitch}>
            <input
              type="text"
              value={adminLeagueId}
              onChange={event => setAdminLeagueId(event.target.value)}
              placeholder="Enter league id"
            />
            <button type="submit">Switch league</button>
          </form>
          {adminStatus && <p className="admin-status">{adminStatus}</p>}
        </section>

        <section className="team-pick">
          <div className="team-pick-header">
            <h2>Select your team</h2>
            <p>We will use this to resolve "my team" prompts.</p>
          </div>

          <div className="team-grid">
            {teamOptions.length === 0 && (
              <div className="team-card loading">Loading rosters...</div>
            )}
            {teamOptions.map(option => (
              <button
                key={option.ownerId}
                type="button"
                className="team-card"
                onClick={() => handleTeamSelect(option)}
              >
                <span className="team-name">{option.displayName}</span>
                {option.teamName && (
                  <span className="team-subtitle">{option.teamName}</span>
                )}
              </button>
            ))}
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero-title">
          <p className="hero-kicker">GridironGPT</p>
          <h1>Fantasy Football AI Assistant</h1>
          <p className="hero-subtitle">
            Type a matchup request, we will call your AI service layer and return a clear edge.
          </p>
        </div>
        {healthError && <p className="hero-error">Health check failed: {healthError}</p>}
      </header>

      <main className="chat-card">
        <div className="chat-header">
          <div className="chat-title-row">
            <div>
              <h2>Live roster chat</h2>
              <p>Compare two owners by name and week.</p>
            </div>
            <button type="button" className="back-button" onClick={handleTeamReset}>
              Change team
            </button>
          </div>
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
              <p>Crunching projections and lineup edges</p>
            </div>
          )}
        </div>

        <form className="chat-input" onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={event => setInput(event.target.value)}
            placeholder="compare user1 vs user2 week 7"
          />
          <button type="submit" disabled={isLoading}>
            Compare
          </button>
        </form>

        {teamOptions.length > 0 && (
          <div className="chat-hints">
            {teamOptions.map(option => (
              <button
                key={option.ownerId}
                type="button"
                onClick={() => handleTeamSelect(option)}
              >
                {option.displayName}
              </button>
            ))}
          </div>
        )}

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
