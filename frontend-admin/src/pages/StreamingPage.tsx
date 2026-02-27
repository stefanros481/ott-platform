import SimLivePanel from '@/components/SimLivePanel'
import TSTVRulesPanel from '@/components/TSTVRulesPanel'

export default function StreamingPage() {
  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Streaming</h1>

      <div className="space-y-8">
        <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <SimLivePanel />
        </section>

        <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <TSTVRulesPanel />
        </section>
      </div>
    </div>
  )
}
