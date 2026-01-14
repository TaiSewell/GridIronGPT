import { useEffect, useMemo, useState } from 'react'
import './App.css'

const API_BASE = (import.meta.env.VITE_API_BASE || 'http://localhost:8000')

const STARTER_HINTS = [
  'compare Etac vs JDose week 10',
  'compare Tai versus JDOse week 12 include bench',
  'compare my team vs Etac week 9',
  'who should I start this week 7',
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
  } catch (err) {
    result = null
  }
  return result
}

function storeTeamSelection(team) {
  let success = false
  try {
    localStorage.setItem(LOCAL_TEAM_KEY, JSON.stringify(team))
    success = true
  } catch (err) {
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
      result.error = 'Add a number, e.g. "give me the top 10 players this year".'
    } else if (limitValue < 1 || limitValue > 100) {
      result.error = 'Pick a limit between 1 and 100.'
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
    return { error: 'Try "compare Alice vs Bob week 7".' }
  }

  const userA = compareMatch[1].trim()
  const userB = compareMatch[2].trim()
  if (!userA || !userB) {
    return { error: 'I need two roster names to compare.' }
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
    if (!week) {
      result.error = 'Add a week, e.g. "who should I start for jdose week 7".'
    } else if (!userA) {
      result.error = 'Add a roster name, e.g. "who should I start for jdose week 7".'
    } else {
      result.userA = userA
      result.week = week
    }
  }
  return result
}

export default function App() {
  const [health, setHealth] = useState(null)
  const [healthError, setHealthError] = useState(null)
  const [myTeam, setMyTeam] = useState(() => loadStoredTeam())
  const [teamOptions, setTeamOptions] = useState([])
  const [pendingInput, setPendingInput] = useState('')
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Ask me questions based on your fantasy league. I will do my best to assist you!'
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
        { role: 'system', content: 'Try either league summary or top players, not both.' }
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

    const startSitParsed = fantasyParsed.intent
      ? { intent: false }
      : parseStartSitPrompt(inputText)
    if (startSitParsed.intent && startSitParsed.error) {
      setMessages(prev => [...prev, { role: 'system', content: startSitParsed.error }])
      return
    }

    const parsed = fantasyParsed.intent || startSitParsed.intent
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
            <h1>Welcome to GridironGPT</h1>
            <p className="hero-subtitle">
              Select your team to personalize your league insights and unlock your chat.
            </p>
          </div>
          <img
            className="welcome-logo"
            src="../assets/GridIronGPT_Logo.png"
            alt="GridironGPT logo"
          />
          <div className="hero-status">
            <span className={`pill ${health ? 'pill-online' : 'pill-offline'}`}>
              {health ? 'API online' : 'API offline'}
            </span>
            <span className="pill pill-quiet">{apiLabel}</span>
          </div>
          {healthError && <p className="hero-error">Health check failed: {healthError}</p>}
        </header>

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
