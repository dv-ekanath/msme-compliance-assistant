import { useCallback, useEffect, useRef, useState } from 'react'

// Minimal ambient types for the Web Speech API -- not in tsconfig's `lib`
// and no @types package is installed for it, so only the ~4 members this
// hook actually uses are declared here rather than pulling in a package.
interface SpeechRecognitionResultLike {
  0: { transcript: string }
}
interface SpeechRecognitionEventLike {
  results: ArrayLike<SpeechRecognitionResultLike>
}
interface SpeechRecognitionErrorEventLike {
  error: string
}
interface SpeechRecognitionLike {
  lang: string
  interimResults: boolean
  continuous: boolean
  start(): void
  stop(): void
  onresult: ((e: SpeechRecognitionEventLike) => void) | null
  onerror: ((e: SpeechRecognitionErrorEventLike) => void) | null
  onend: (() => void) | null
}
type SpeechRecognitionCtor = new () => SpeechRecognitionLike

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionCtor
    webkitSpeechRecognition?: SpeechRecognitionCtor
  }
}

const Ctor: SpeechRecognitionCtor | null =
  typeof window !== 'undefined' ? (window.SpeechRecognition ?? window.webkitSpeechRecognition ?? null) : null

export const isSpeechRecognitionSupported = Ctor !== null

export type VoiceLanguage = 'en-IN' | 'hi-IN'

export function useSpeechRecognition({ lang, onResult }: { lang: VoiceLanguage; onResult: (transcript: string) => void }) {
  const [listening, setListening] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null)

  const start = useCallback(() => {
    if (!Ctor) {
      setError('Voice input is not supported in this browser.')
      return
    }
    setError(null)
    const recognition = new Ctor()
    recognition.lang = lang
    recognition.interimResults = false
    recognition.continuous = false
    recognition.onresult = (e) => {
      const transcript = e.results[e.results.length - 1][0].transcript
      onResult(transcript)
    }
    recognition.onerror = (e) => {
      setError(e.error === 'not-allowed' ? 'Microphone access was denied.' : 'Voice input failed. Please try again.')
      setListening(false)
    }
    recognition.onend = () => setListening(false)

    recognitionRef.current = recognition
    recognition.start()
    setListening(true)
  }, [lang, onResult])

  const stop = useCallback(() => {
    recognitionRef.current?.stop()
  }, [])

  useEffect(() => {
    return () => recognitionRef.current?.stop()
  }, [])

  return { start, stop, listening, error, supported: isSpeechRecognitionSupported }
}
