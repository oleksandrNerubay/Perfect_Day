import './BottomPanel.css'

// Secondary control slots — extend this array to add/remove flanking buttons
const SECONDARY_CONTROLS = [
  { id: 'history', label: 'History', side: 'left'  },
  { id: 'my-plan', label: 'My Plan', side: 'right' },
  { id: 'vendors', label: 'Vendors', side: 'right' },
]

function MicIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" width="26" height="26" aria-hidden="true">
      <rect x="8.5" y="2" width="7" height="11" rx="3.5" fill="currentColor" />
      <path d="M4 11.5a8 8 0 0 0 16 0" stroke="currentColor" strokeWidth="2"
            strokeLinecap="round" fill="none" />
      <line x1="12" y1="19.5" x2="12" y2="22"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="9"  y1="22"   x2="15" y2="22"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function StopIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" width="22" height="22" aria-hidden="true">
      <rect x="5" y="5" width="14" height="14" rx="3" />
    </svg>
  )
}

export default function BottomPanel({ agentState, onMicPress }) {
  const isListening = agentState === 'listening'
  const isSpeaking  = agentState === 'speaking'

  const leftControls  = SECONDARY_CONTROLS.filter(c => c.side === 'left')
  const rightControls = SECONDARY_CONTROLS.filter(c => c.side === 'right')

  return (
    <div className="bottom-panel">
      <div className="controls-row">
        <div className="secondary-group secondary-group--left">
          {leftControls.map(ctrl => (
            <button
              key={ctrl.id}
              className="secondary-btn"
              onClick={() => console.log(`${ctrl.id} pressed`)}
              aria-label={ctrl.label}
            >
              {ctrl.label}
            </button>
          ))}
        </div>

        <button
          className={[
            'mic-btn',
            isListening ? 'mic-btn--listening' : '',
            isSpeaking  ? 'mic-btn--speaking'  : '',
          ].filter(Boolean).join(' ')}
          onClick={onMicPress}
          aria-label={isListening ? 'Stop listening' : isSpeaking ? 'Stop' : 'Talk to agent'}
        >
          {isListening || isSpeaking ? <StopIcon /> : <MicIcon />}
        </button>

        <div className="secondary-group secondary-group--right">
          {rightControls.map(ctrl => (
            <button
              key={ctrl.id}
              className="secondary-btn"
              onClick={() => console.log(`${ctrl.id} pressed`)}
              aria-label={ctrl.label}
            >
              {ctrl.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
