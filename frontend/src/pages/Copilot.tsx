import { useState, type FormEvent } from 'react'
import { useParams } from 'react-router-dom'
import Nav from '../components/Nav'
import { useSpeechRecognition, type VoiceLanguage } from '../hooks/useSpeechRecognition'
import { askCopilot } from '../lib/api'
import type { CopilotAskResponse } from '../types'

const VOICE_LANGUAGES: { value: VoiceLanguage; label: string }[] = [
  { value: 'en-IN', label: 'English' },
  { value: 'hi-IN', label: 'हिन्दी' },
]

// Phrased with the specific regulatory keywords the seeded demo corpus
// actually uses -- generic questions like "Which compliances apply to my
// business?" don't share enough vocabulary with any one chunk to clear
// the retrieval similarity threshold, so they come back "not grounded"
// even though the corpus has a good, specific answer available.
const SUGGESTED_QUESTIONS = [
  'What is the GST registration threshold?',
  'When is the GST monthly return due?',
  'What is the EPF employee threshold for applicability?',
  'What is Udyam registration and why should I get it?',
]

interface Exchange {
  question: string
  response: CopilotAskResponse | null
  error: string | null
  loading: boolean
}

const CONFIDENCE_STYLES: Record<string, string> = {
  high: 'bg-emerald-100 text-emerald-700',
  medium: 'bg-amber-100 text-amber-700',
  low: 'bg-slate-100 text-slate-600',
}

export default function Copilot() {
  const { businessId } = useParams<{ businessId: string }>()
  const [question, setQuestion] = useState('')
  const [exchanges, setExchanges] = useState<Exchange[]>([])
  const [voiceLang, setVoiceLang] = useState<VoiceLanguage>('en-IN')
  const voice = useSpeechRecognition({ lang: voiceLang, onResult: setQuestion })

  async function submitQuestion(q: string) {
    const trimmed = q.trim()
    if (!businessId || !trimmed) return

    const index = exchanges.length
    setExchanges((prev) => [...prev, { question: trimmed, response: null, error: null, loading: true }])
    setQuestion('')

    try {
      const response = await askCopilot(businessId, trimmed)
      setExchanges((prev) => prev.map((e, i) => (i === index ? { ...e, response, loading: false } : e)))
    } catch {
      setExchanges((prev) =>
        prev.map((e, i) =>
          i === index
            ? { ...e, error: 'Could not reach the Copilot. Please try again.', loading: false }
            : e,
        ),
      )
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    submitQuestion(question)
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-1 text-xl font-semibold">Compliance Copilot</h1>
        <p className="mb-6 text-sm text-slate-500">
          Ask about your obligations. Every answer is grounded in retrieved regulatory evidence and
          your Digital Twin, not the AI's own knowledge — the deterministic Rules Engine, not the AI,
          decides what applies to your business.
        </p>

        {exchanges.length === 0 && (
          <div className="mb-6">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">
              Suggested questions
            </p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => submitQuestion(q)}
                  className="rounded-full border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 hover:border-slate-400"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-5">
          {exchanges.map((exchange, i) => (
            <AnswerCard key={i} exchange={exchange} />
          ))}
        </div>

        <form
          onSubmit={handleSubmit}
          className="sticky bottom-6 mt-6 flex gap-2 rounded-lg border border-slate-200 bg-white p-2 shadow-sm"
        >
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask about your compliance obligations…"
            className="flex-1 rounded-md border-none px-3 py-2 text-sm focus:outline-none"
          />
          {voice.supported && (
            <>
              <select
                value={voiceLang}
                onChange={(e) => setVoiceLang(e.target.value as VoiceLanguage)}
                className="rounded-md border border-slate-200 px-2 text-sm text-slate-600"
                aria-label="Voice input language"
              >
                {VOICE_LANGUAGES.map((l) => (
                  <option key={l.value} value={l.value}>
                    {l.label}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => (voice.listening ? voice.stop() : voice.start())}
                aria-label={voice.listening ? 'Stop voice input' : 'Ask by voice'}
                title={voice.listening ? 'Stop voice input' : 'Ask by voice'}
                className={`rounded-md px-3 py-2 text-sm font-medium ${
                  voice.listening
                    ? 'bg-red-100 text-red-700'
                    : 'border border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                {voice.listening ? '● Listening…' : '🎤'}
              </button>
            </>
          )}
          <button
            type="submit"
            disabled={!question.trim()}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-40"
          >
            Ask
          </button>
        </form>
        {voice.error && <p className="mt-2 text-sm text-red-600">{voice.error}</p>}
      </main>
    </div>
  )
}

function AnswerCard({ exchange }: { exchange: Exchange }) {
  const { question, response, error, loading } = exchange

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <p className="mb-3 text-sm font-medium text-slate-500">You asked: "{question}"</p>

      {loading && <p className="text-sm text-slate-400">Retrieving evidence and generating an answer…</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}

      {response && (
        <>
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                response.grounded ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'
              }`}
            >
              {response.grounded ? 'Grounded in retrieved evidence' : 'Not grounded — insufficient evidence'}
            </span>
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-medium ${CONFIDENCE_STYLES[response.confidence]}`}
            >
              Confidence: {response.confidence}
            </span>
          </div>

          {response.requires_verification && (
            <div className="mb-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
              This answer relies on demo/unreviewed source content and has not been legally verified.
              Confirm with the cited source(s) or a compliance professional before relying on it.
            </div>
          )}

          <p className="mb-4 whitespace-pre-wrap text-sm text-slate-800">{response.answer}</p>

          {response.citations.length > 0 && (
            <div className="rounded-md border border-slate-100 bg-slate-50 p-3">
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">
                Regulatory sources cited
              </p>
              <ul className="space-y-2">
                {response.citations.map((c) => (
                  <li key={c.source_id} className="text-sm">
                    <a
                      href={c.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="font-medium text-slate-800 underline hover:text-slate-950"
                    >
                      {c.title}
                    </a>
                    <span className="text-slate-500">
                      {' '}
                      — {c.authority}
                      {c.section ? `, ${c.section}` : ''} · relevance {Math.round(c.relevance_score * 100)}%
                      {c.status !== 'verified' ? ` · ${c.status}, unverified` : ''}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  )
}
