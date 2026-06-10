import { useState } from 'react'
import AgentFace from './components/AgentFace/AgentFace'
import BottomPanel from './components/BottomPanel/BottomPanel'
import TopMenu from './components/TopMenu/TopMenu'

// Caption text shown during speaking state
const AGENT_CAPTIONS = {
  idle:      '',
  listening: '',
  thinking:  '',
  speaking:  "Hello! I'm here to help you plan your perfect day. What kind of event are you imagining?",
}

// Demo cycle driven by the mic button
const STATE_CYCLE = ['idle', 'listening', 'thinking', 'speaking']

export default function App() {
  const [agentState, setAgentState] = useState('idle')

  const handleMicPress = () => {
    setAgentState(prev => {
      const next = (STATE_CYCLE.indexOf(prev) + 1) % STATE_CYCLE.length
      return STATE_CYCLE[next]
    })
  }

  return (
    <div className="app-root">
      <TopMenu />

      <main className="center-stage">
        <AgentFace
          agentState={agentState}
          caption={AGENT_CAPTIONS[agentState]}
        />
      </main>

      <BottomPanel agentState={agentState} onMicPress={handleMicPress} />
    </div>
  )
}
