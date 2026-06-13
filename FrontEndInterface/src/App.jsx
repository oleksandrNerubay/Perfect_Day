import { useState, useRef, useCallback } from 'react'
import AgentFace from './components/AgentFace/AgentFace'
import TopMenu from './components/TopMenu/TopMenu'

// Local representative image (public/representative.png)
const AVATAR_IMAGE = '/representative.png'

// Stub latency that simulates backend generation time
const STUB_LATENCY_MS = 2000

// Stub responses drawn from QA.md knowledge base.
// The lip-sync engine animates every word in these answers.
// Replace requestResponse() with a real fetch() once the backend is wired.
const STUB_RESPONSES = [
  "Hello! I'm here to help you plan your perfect day. Perfect Day is an AI-driven event planning and deal discovery platform — it consolidates planning, vendor discovery, scheduling, budgeting, and deal access into one personalized experience. What kind of event are you imagining?",
  "Our one-click planning feature reads your location and saved preferences, then generates a full day's itinerary automatically. You can adjust any part before you start. It works just as well for a simple afternoon out with friends as it does for a full wedding.",
  "Perfect Day partners with a wide range of businesses — local venues, caterers, decorators, entertainment providers, and major brands. Partner deals and exclusive offers surface automatically as you build your itinerary, based on your preferences and location.",
  "The app uses a freemium model. Core features are completely free. Premium features — advanced planning tools, enhanced personalization, analytics, and more — are available through a paid subscription. There are no hidden fees; all costs are shown clearly before you commit.",
  "Perfect Day supports real-time collaboration, so planning committees, families, or teams can work on the same event simultaneously. Role-based access lets you delegate tasks while keeping sensitive details under control.",
]

// ── State / data contract ────────────────────────────────────────────
//   agentState  'idle' | 'listening' | 'thinking' | 'speaking'
//   videoUrl    string | null  — talking-head clip from backend (null = lip-sync only)
//   caption     string         — response text driving both caption and lip sync

export default function App() {
  const [agentState, setAgentState] = useState('idle')
  const [videoUrl,   setVideoUrl]   = useState(null)
  const [caption,    setCaption]    = useState('')
  const responseIndexRef = useRef(0)

  // Simulates the backend round-trip.
  // In production: replace with fetch('/api/respond', { body: input })
  // and set videoUrl to the returned talking-head clip URL.
  const requestResponse = useCallback(async (_input) => {
    setAgentState('thinking')
    setVideoUrl(null)   // no external video in stub — lip-sync carries the speaking state
    setCaption('')

    await new Promise(r => setTimeout(r, STUB_LATENCY_MS))

    const text = STUB_RESPONSES[responseIndexRef.current % STUB_RESPONSES.length]
    responseIndexRef.current++

    setCaption(text)
    setAgentState('speaking')
  }, [])

  const handleMicPress = useCallback(() => {
    if (agentState === 'idle') {
      setAgentState('listening')
    } else if (agentState === 'listening') {
      requestResponse('user input placeholder')
    } else {
      // Interrupt thinking or speaking
      setAgentState('idle')
      setVideoUrl(null)
      setCaption('')
    }
  }, [agentState, requestResponse])

  // Called when the talking-head clip finishes (no-op in stub since videoUrl is null)
  const handleVideoEnd = useCallback(() => {
    setAgentState('idle')
    setVideoUrl(null)
    setCaption('')
  }, [])

  return (
    <div className="app-root">
      <TopMenu />

      <main className="center-stage">
        <AgentFace
          agentState={agentState}
          avatarImage={AVATAR_IMAGE}
          videoUrl={videoUrl}
          caption={caption}
          onVideoEnd={handleVideoEnd}
          onMicPress={handleMicPress}
        />
      </main>
    </div>
  )
}
