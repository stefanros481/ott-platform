import { useState, useEffect, useRef } from 'react'
import {
  submitQuery,
  pollJob,
  type ActiveQueryState,
  type HistoryEntry,
  type QueryResult,
} from '@/api/analytics'
import { ApiError } from '@/api/client'

// ── Example queries (T015) ────────────────────────────────────────────────────

const EXAMPLE_QUERIES = [
  {
    category: 'Revenue & Engagement',
    questions: [
      'Which genres drive SVoD revenue?',
      'What are the top titles by completion rate?',
      'Show me revenue growth by genre over time',
    ],
  },
  {
    category: 'Regional & Audience',
    questions: [
      'Show regional content preferences in Norway',
      'Which content trends with kids profiles?',
      'Show regional content preferences across Norway, Sweden and Denmark',
    ],
  },
  {
    category: 'Service & Behaviour',
    questions: [
      'How does engagement differ between Linear TV and SVoD?',
      'What is the Cloud PVR impact on viewing?',
      'Show me browse-without-watch patterns',
      'What are the SVoD upgrade signals?',
    ],
  },
]

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatColumnHeader(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function AnalyticsPage() {
  const [question, setQuestion] = useState<string>('')
  const [activeQueryState, setActiveQueryState] = useState<ActiveQueryState>({ phase: 'idle' })
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // ── T007: onSubmit handler ────────────────────────────────────────────────

  async function onSubmit() {
    if (!question.trim()) return
    setActiveQueryState({ phase: 'submitting' })
    try {
      const response = await submitQuery(question)
      if (response.status === 'complete' && response.result) {
        setActiveQueryState({ phase: 'complete', result: response.result })
      } else if (response.status === 'clarification' && response.clarification) {
        // do NOT reset question state — textarea retains original text for editing
        setActiveQueryState({ phase: 'clarification', payload: response.clarification })
      } else if (response.status === 'pending' && response.job_id) {
        setActiveQueryState({ phase: 'polling', jobId: response.job_id })
      }
    } catch (err) {
      if (err instanceof ApiError || err instanceof Error) {
        setActiveQueryState({ phase: 'failed', errorMessage: err.message })
      } else {
        setActiveQueryState({ phase: 'failed', errorMessage: 'Unable to reach the analytics service. Please try again.' })
      }
    }
  }

  // ── T011 + T012: Polling useEffect ────────────────────────────────────────

  useEffect(() => {
    if (activeQueryState.phase !== 'polling') return
    const { jobId } = activeQueryState

    const intervalId = setInterval(async () => {
      try {
        const job = await pollJob(jobId)
        if (job.status === 'complete' && job.result) {
          clearInterval(intervalId)
          clearTimeout(timeoutId)
          setActiveQueryState({ phase: 'complete', result: job.result })
        } else if (job.status === 'failed') {
          clearInterval(intervalId)
          clearTimeout(timeoutId)
          setActiveQueryState({ phase: 'failed', errorMessage: job.error_message ?? 'Query failed' })
        }
      } catch {
        // keep polling — transient network error
      }
    }, 2000)

    const timeoutId = setTimeout(() => {
      clearInterval(intervalId)
      setActiveQueryState({ phase: 'timeout' })
    }, 60000)

    return () => {
      clearInterval(intervalId)
      clearTimeout(timeoutId)
    }
  }, [activeQueryState.phase === 'polling' ? activeQueryState.jobId : null])

  // ── T017: Append to history when reaching terminal state ──────────────────

  useEffect(() => {
    const s = activeQueryState
    if (s.phase === 'complete') {
      setHistory((prev) => [
        {
          id: crypto.randomUUID(),
          question,
          submittedAt: new Date(),
          status: 'complete',
          result: s.result,
          clarification: null,
          errorMessage: null,
        },
        ...prev,
      ])
    } else if (s.phase === 'clarification') {
      setHistory((prev) => [
        {
          id: crypto.randomUUID(),
          question,
          submittedAt: new Date(),
          status: 'clarification',
          result: null,
          clarification: s.payload,
          errorMessage: null,
        },
        ...prev,
      ])
    } else if (s.phase === 'failed') {
      setHistory((prev) => [
        {
          id: crypto.randomUUID(),
          question,
          submittedAt: new Date(),
          status: 'failed',
          result: null,
          clarification: null,
          errorMessage: s.errorMessage,
        },
        ...prev,
      ])
    } else if (s.phase === 'timeout') {
      setHistory((prev) => [
        {
          id: crypto.randomUUID(),
          question,
          submittedAt: new Date(),
          status: 'failed',
          result: null,
          clarification: null,
          errorMessage: 'Query timed out.',
        },
        ...prev,
      ])
    }
    // We only want this to fire when phase changes to a terminal state
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeQueryState.phase])

  // ── Disable condition (T019) ──────────────────────────────────────────────

  const isSubmitDisabled =
    question.trim() === '' ||
    activeQueryState.phase === 'submitting' ||
    activeQueryState.phase === 'polling'

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div>
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Analytics</h1>
        <p className="mt-1 text-sm text-gray-500">Ask a question about your content performance</p>
      </div>

      {/* Two-column layout */}
      <div className="flex gap-6">
        {/* Left column — examples + history */}
        <div className="w-72 shrink-0 space-y-6">
          <ExamplesPanel
            onSelect={(q) => {
              setQuestion(q)
              textareaRef.current?.focus()
            }}
          />
          <QueryHistory
            history={history}
            onSelect={(entry) => {
              setQuestion(entry.question)
              if (entry.status === 'complete' && entry.result) {
                setActiveQueryState({ phase: 'complete', result: entry.result })
              } else if (entry.status === 'clarification' && entry.clarification) {
                setActiveQueryState({ phase: 'clarification', payload: entry.clarification })
              } else if (entry.status === 'failed') {
                setActiveQueryState({ phase: 'failed', errorMessage: entry.errorMessage ?? 'Query failed' })
              }
            }}
          />
        </div>

        {/* Right column — query input + result panel */}
        <div className="flex-1 space-y-4">
          {/* Query input */}
          <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <textarea
              ref={textareaRef}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question about your content performance…"
              rows={3}
              className="w-full resize-none rounded-lg border border-gray-200 p-3 text-sm text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            <div className="mt-3 flex justify-end">
              <button
                onClick={onSubmit}
                disabled={isSubmitDisabled}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Submit
              </button>
            </div>
          </div>

          {/* Result panel */}
          <ResultPanel state={activeQueryState} onRetry={() => setActiveQueryState({ phase: 'idle' })} />
        </div>
      </div>
    </div>
  )
}

// ── ResultPanel ───────────────────────────────────────────────────────────────

function ResultPanel({
  state,
  onRetry,
}: {
  state: ActiveQueryState
  onRetry: () => void
}) {
  // T023: idle state
  if (state.phase === 'idle') {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 bg-white py-16 text-center">
        <SearchIcon />
        <p className="mt-3 text-sm text-gray-400">
          Type a question above to get started — or pick an example from the left.
        </p>
      </div>
    )
  }

  // T013a: submitting
  if (state.phase === 'submitting') {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-gray-200 bg-white py-16">
        <Spinner />
        <p className="mt-3 text-sm text-gray-500">Submitting…</p>
      </div>
    )
  }

  // T013b: polling
  if (state.phase === 'polling') {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-gray-200 bg-white py-16">
        <Spinner />
        <p className="mt-3 text-sm text-gray-500">Analysing your question…</p>
        <p className="mt-1 text-xs text-gray-400">This may take a few seconds</p>
      </div>
    )
  }

  // T013c: timeout
  if (state.phase === 'timeout') {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-6">
        <p className="text-sm font-medium text-amber-900">The query is taking longer than expected.</p>
        <p className="mt-1 text-xs text-amber-700">The job may still be processing. You can retry or try a simpler question.</p>
        <button onClick={onRetry} className="mt-4 rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700">
          Retry
        </button>
      </div>
    )
  }

  // T014: clarification
  if (state.phase === 'clarification') {
    return (
      <div className="rounded-xl bg-amber-50 border border-amber-200 p-4">
        <div className="flex items-center gap-2">
          <InfoIcon />
          <h3 className="text-sm font-semibold text-amber-900">Could you be more specific?</h3>
        </div>
        <p className="mt-2 text-sm text-amber-900">{state.payload.clarifying_question}</p>
        <p className="mt-1 text-xs text-amber-700">{state.payload.context}</p>
      </div>
    )
  }

  // T020: failed
  if (state.phase === 'failed') {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6">
        <p className="text-sm font-medium text-red-900">{state.errorMessage}</p>
        <button onClick={onRetry} className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700">
          Retry
        </button>
      </div>
    )
  }

  // T008 + T009 + T010: complete
  if (state.phase === 'complete') {
    return <ResultCard result={state.result} />
  }

  return null
}

// ── ResultCard (T008 + T009 + T010) ──────────────────────────────────────────

function ResultCard({ result }: { result: QueryResult }) {
  const pct = Math.round(result.confidence * 100)
  const badgeClass =
    pct >= 80
      ? 'bg-green-100 text-green-800'
      : pct >= 65
      ? 'bg-amber-100 text-amber-800'
      : 'bg-red-100 text-red-800'

  const firstRow = result.data[0]
  const columns = firstRow ? Object.keys(firstRow) : []

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      {/* Summary + confidence badge */}
      <div className="flex items-start gap-3">
        <p className="flex-1 text-sm text-gray-800">{result.summary}</p>
        <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold ${badgeClass}`}>
          {pct}% confidence
        </span>
      </div>

      {/* Data table */}
      <div className="mt-4">
        {result.data.length === 0 ? (
          <p className="text-sm text-gray-500">No data found for this query.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead>
                <tr>
                  {columns.map((col) => (
                    <th
                      key={col}
                      className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-gray-500"
                    >
                      {formatColumnHeader(col)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {result.data.map((row, i) => (
                  <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    {columns.map((col) => (
                      <td key={col} className="px-4 py-2 text-gray-700">
                        {String(row[col] ?? '–')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Metadata footer */}
      <div className="mt-4 space-y-1 border-t border-gray-100 pt-4 text-xs text-gray-500">
        <div>
          <span className="font-medium text-gray-700">Applied filters: </span>
          region: {result.applied_filters.region ?? '–'} · time period:{' '}
          {result.applied_filters.time_period ?? '–'} · service:{' '}
          {result.applied_filters.service_type ?? '–'}
        </div>
        <div>
          <span className="font-medium text-gray-700">Data sources: </span>
          {result.data_sources.join(', ')}
        </div>
        <div>
          <span className="font-medium text-gray-700">Coverage: </span>
          from {new Date(result.coverage_start).toLocaleDateString()} · freshness:{' '}
          {new Date(result.data_freshness).toLocaleDateString()}
        </div>
      </div>
    </div>
  )
}

// ── ExamplesPanel (T015 + T016) ───────────────────────────────────────────────

function ExamplesPanel({ onSelect }: { onSelect: (q: string) => void }) {
  return (
    <div>
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">
        Example Questions
      </h2>
      <div className="space-y-4">
        {EXAMPLE_QUERIES.map((group) => (
          <div key={group.category}>
            <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400">
              {group.category}
            </p>
            <ul className="space-y-0.5">
              {group.questions.map((q) => (
                <li key={q}>
                  <button
                    onClick={() => onSelect(q)}
                    className="w-full rounded px-2 py-1 text-left text-sm text-gray-700 hover:bg-indigo-50 hover:text-indigo-600"
                  >
                    {q}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── QueryHistory (T017 + T018) ────────────────────────────────────────────────

function QueryHistory({
  history,
  onSelect,
}: {
  history: HistoryEntry[]
  onSelect: (entry: HistoryEntry) => void
}) {
  if (history.length === 0) return null

  return (
    <div>
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">
        Recent Queries
      </h2>
      <ul className="space-y-0.5 overflow-y-auto">
        {history.map((entry) => (
          <li key={entry.id}>
            <button
              onClick={() => onSelect(entry)}
              className="w-full rounded px-2 py-1.5 text-left hover:bg-gray-50"
            >
              <p className="truncate text-sm text-gray-700">{entry.question}</p>
              <p className="text-xs text-gray-400">
                {new Date(entry.submittedAt).toLocaleTimeString()}
              </p>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

// ── SVG helpers ───────────────────────────────────────────────────────────────

function Spinner() {
  return (
    <svg
      className="h-8 w-8 animate-spin text-indigo-600"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  )
}

function SearchIcon() {
  return (
    <svg className="h-10 w-10 text-gray-300" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 15.803a7.5 7.5 0 0 0 10.607 0Z" />
    </svg>
  )
}

function InfoIcon() {
  return (
    <svg className="h-4 w-4 shrink-0 text-amber-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" />
    </svg>
  )
}
