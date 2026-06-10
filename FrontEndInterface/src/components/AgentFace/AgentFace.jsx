import { useState, useEffect } from 'react'
import './AgentFace.css'

// SVG mouth paths for each agent state
const MOUTH = {
  idle:            'M 82 150 Q 120 164 158 150',
  listening:       'M 78 147 Q 120 167 162 147',
  speaking_open:   'M 87 143 Q 120 173 153 143',
  speaking_closed: 'M 87 149 Q 120 158 153 149',
  thinking:        'M 92 153 Q 120 150 148 153',
}

// Eye vertical radius per state (horizontal radius is fixed at 20)
const EYE_RY = { idle: 7, listening: 13, speaking: 9, thinking: 8 }

// Eyebrow paths per state (left/right SVG path D attributes)
const BROWS = {
  idle: {
    left:  'M 70 80 Q 83 75 96 79',
    right: 'M 144 79 Q 157 75 170 80',
  },
  listening: {
    left:  'M 70 77 Q 83 72 96 76',
    right: 'M 144 76 Q 157 72 170 77',
  },
  speaking: {
    left:  'M 70 78 Q 83 73 96 77',
    right: 'M 144 77 Q 157 73 170 78',
  },
  thinking: {
    left:  'M 70 74 Q 83 70 96 78',
    right: 'M 144 79 Q 157 72 170 76',
  },
}

export default function AgentFace({ agentState = 'idle', caption = '' }) {
  const [mouthOpen, setMouthOpen] = useState(false)
  const [blinking, setBlinking] = useState(false)

  // Animate mouth while speaking
  useEffect(() => {
    if (agentState !== 'speaking') { setMouthOpen(false); return }
    const id = setInterval(() => setMouthOpen(v => !v), 175)
    return () => clearInterval(id)
  }, [agentState])

  // Random idle blink
  useEffect(() => {
    if (agentState !== 'idle') { setBlinking(false); return }
    let timerId
    const scheduleBlink = () => {
      timerId = setTimeout(() => {
        setBlinking(true)
        timerId = setTimeout(() => { setBlinking(false); scheduleBlink() }, 140)
      }, 2200 + Math.random() * 2800)
    }
    scheduleBlink()
    return () => clearTimeout(timerId)
  }, [agentState])

  const eyeRY    = blinking ? 1 : EYE_RY[agentState]
  const brows    = BROWS[agentState]
  const mouthPath =
    agentState === 'speaking'
      ? mouthOpen ? MOUTH.speaking_open : MOUTH.speaking_closed
      : MOUTH[agentState]
  const mouthFill = agentState === 'speaking' && mouthOpen
    ? 'var(--color-face-brow)'
    : 'none'

  return (
    <div className={`agent-face state-${agentState}`}>
      {agentState === 'listening' && (
        <div className="pulse-rings" aria-hidden="true">
          <div className="pulse-ring" />
          <div className="pulse-ring pulse-ring--delayed" />
        </div>
      )}

      <svg
        className="agent-svg"
        viewBox="0 0 240 240"
        xmlns="http://www.w3.org/2000/svg"
        role="img"
        aria-label={`Agent is ${agentState}`}
      >
        <defs>
          <radialGradient id="faceGrad" cx="42%" cy="38%" r="62%">
            <stop offset="0%"   stopColor="var(--color-face-skin)" />
            <stop offset="100%" stopColor="var(--color-face-skin-shadow)" />
          </radialGradient>
          <radialGradient id="blushGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="var(--color-face-blush)" stopOpacity="0.5" />
            <stop offset="100%" stopColor="var(--color-face-blush)" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Face base */}
        <circle cx="120" cy="120" r="108" fill="url(#faceGrad)" />

        {/* Blush marks */}
        <ellipse cx="62"  cy="142" rx="22" ry="12" fill="url(#blushGrad)" />
        <ellipse cx="178" cy="142" rx="22" ry="12" fill="url(#blushGrad)" />

        {/* Eyebrows */}
        <path d={brows.left}  className="eyebrow" />
        <path d={brows.right} className="eyebrow" />

        {/* Left eye */}
        <ellipse cx="83" cy="102" rx="20" ry={eyeRY + 5} fill="white" />
        {!blinking && (
          <>
            <ellipse cx="85"  cy="104" rx="12"  ry={eyeRY}          fill="var(--color-face-iris)" />
            <ellipse cx="86"  cy="104" rx="5.5" ry={eyeRY * 0.5}    fill="var(--color-bg)" />
            <ellipse cx="89"  cy="99"  rx="3.5" ry="2.5"            fill="white" opacity="0.9" />
          </>
        )}

        {/* Right eye */}
        <ellipse cx="157" cy="102" rx="20" ry={eyeRY + 5} fill="white" />
        {!blinking && (
          <>
            <ellipse cx="159" cy="104" rx="12"  ry={eyeRY}          fill="var(--color-face-iris)" />
            <ellipse cx="160" cy="104" rx="5.5" ry={eyeRY * 0.5}    fill="var(--color-bg)" />
            <ellipse cx="163" cy="99"  rx="3.5" ry="2.5"            fill="white" opacity="0.9" />
          </>
        )}

        {/* Mouth */}
        <path
          d={mouthPath}
          fill={mouthFill}
          stroke="var(--color-face-brow)"
          strokeWidth="4"
          strokeLinecap="round"
        />

        {/* Thinking dots (inside face, below mouth) */}
        {agentState === 'thinking' && (
          <>
            <circle cx="104" cy="170" r="5" fill="var(--color-face-brow)" className="dot dot-1" />
            <circle cx="120" cy="170" r="5" fill="var(--color-face-brow)" className="dot dot-2" />
            <circle cx="136" cy="170" r="5" fill="var(--color-face-brow)" className="dot dot-3" />
          </>
        )}
      </svg>

      {/* State label */}
      <p className={`state-label state-label--${agentState}`}>
        {agentState === 'listening' && 'Listening…'}
        {agentState === 'thinking'  && 'Thinking…'}
      </p>

      {/* Speech caption */}
      {caption && (
        <div className="agent-caption">
          <p>{caption}</p>
        </div>
      )}
    </div>
  )
}
