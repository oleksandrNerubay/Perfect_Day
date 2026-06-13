import { useState, useEffect, useRef, useCallback } from 'react'
import './AgentFace.css'

// ── Main component ────────────────────────────────────────────────────
export default function AgentFace({ agentState, avatarImage, videoUrl, caption, onVideoEnd, onMicPress }) {
  const videoRef    = useRef(null)
  const [videoReady, setVideoReady] = useState(false)
  const [blinking,   setBlinking]   = useState(false)

  // ── Video preload when URL arrives (starts during 'thinking' for zero-latency play)
  useEffect(() => {
    const vid = videoRef.current
    if (!vid) return
    if (!videoUrl) {
      setVideoReady(false)
      vid.pause()
      vid.removeAttribute('src')
      vid.load()
      return
    }
    setVideoReady(false)
    vid.src = videoUrl
    vid.load()
    const onReady = () => setVideoReady(true)
    vid.addEventListener('canplaythrough', onReady, { once: true })
    return () => vid.removeEventListener('canplaythrough', onReady)
  }, [videoUrl])

  // ── Play once speaking + buffered; pause otherwise
  useEffect(() => {
    const vid = videoRef.current
    if (!vid) return
    if (agentState === 'speaking' && videoReady) {
      vid.play().catch(() => {})
    } else if (agentState !== 'speaking' && !vid.paused) {
      vid.pause()
    }
  }, [agentState, videoReady])

  // ── Random blink while still photo is visible
  useEffect(() => {
    if (agentState === 'speaking' && videoReady) { setBlinking(false); return }
    let tid
    const sched = () => {
      tid = setTimeout(() => {
        setBlinking(true)
        tid = setTimeout(() => { setBlinking(false); sched() }, 130)
      }, 2500 + Math.random() * 3000)
    }
    sched()
    return () => clearTimeout(tid)
  }, [agentState, videoReady])

  const handleVideoEnded = useCallback(() => {
    setVideoReady(false)
    onVideoEnd?.()
  }, [onVideoEnd])

  const showVideo = agentState === 'speaking' && videoReady

  return (
    <div className={`agent-face state-${agentState}`}>

      {/* Listening pulse rings — wrap the entire frame */}
      {agentState === 'listening' && (
        <div className="pulse-rings" aria-hidden="true">
          <div className="pulse-ring" />
          <div className="pulse-ring pulse-ring--delayed" />
        </div>
      )}

      <button className="avatar-frame" onClick={onMicPress} aria-label={
        agentState === 'idle'      ? 'Start listening' :
        agentState === 'listening' ? 'Send' : 'Cancel'
      }>

        {/* State badge (Listening / Thinking) */}
        <p className={`state-badge state-badge--${agentState}`}>
          {agentState === 'listening' && 'Listening…'}
          {agentState === 'thinking'  && 'Thinking…'}
        </p>

        {/* Still photo */}
        <img
          src={avatarImage}
          alt="Perfect Day AI representative"
          className={`avatar-layer avatar-photo${!showVideo ? ' avatar-breathing' : ''}`}
          style={{ opacity: showVideo ? 0 : 1 }}
          draggable={false}
        />

        {/* Blink overlay */}
        <div
          className={`blink-overlay${blinking ? ' blink-overlay--active' : ''}`}
          aria-hidden="true"
        />

        {/* Talking-head video (real backend) */}
        <video
          ref={videoRef}
          className="avatar-layer avatar-video"
          style={{ opacity: showVideo ? 1 : 0 }}
          onEnded={handleVideoEnded}
          playsInline
          preload="none"
        />

        {/* Thinking dots */}
        {agentState === 'thinking' && (
          <div className="thinking-dots" aria-hidden="true">
            <span className="dot dot-1" />
            <span className="dot dot-2" />
            <span className="dot dot-3" />
          </div>
        )}

        {/* Bottom gradient so caption text reads cleanly */}
        <div className="frame-gradient" aria-hidden="true" />

        {/* Response caption — overlaid at bottom of frame */}
        {caption && agentState === 'speaking' && (
          <div className="agent-caption">
            <p>{caption}</p>
          </div>
        )}
      </button>
    </div>
  )
}
