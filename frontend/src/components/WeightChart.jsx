import { useState, useMemo } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import { subDays, subMonths, subYears, format } from 'date-fns'
import Icon from './Icon'
import { EmptyState } from './ui'

const RANGES = [
  { label: '1W', getDates: () => ({ from: subDays(new Date(), 7),   to: new Date() }) },
  { label: '1M', getDates: () => ({ from: subMonths(new Date(), 1), to: new Date() }) },
  { label: '3M', getDates: () => ({ from: subMonths(new Date(), 3), to: new Date() }) },
  { label: '1Y', getDates: () => ({ from: subYears(new Date(), 1),  to: new Date() }) },
  { label: 'All', getDates: () => ({ from: new Date(0),             to: new Date() }) },
]

// One colour per cat — accent for first, then a softer second
const CAT_COLORS = ['var(--chart-line)', 'var(--success)', '#38BDF8', '#F59E0B']

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip__date">{label}</div>
      {payload.map((entry) => (
        <div key={entry.name} className="chart-tooltip__row">
          <span style={{ color: entry.color }}>{entry.name}</span>
          <span>{entry.value.toFixed(3)} kg</span>
        </div>
      ))}
    </div>
  )
}

export default function WeightChart({ weightHistory, onRangeChange, weightLoading = false }) {
  const [activeRange, setActiveRange] = useState('1Y')

  function handleRange(range) {
    setActiveRange(range.label)
    const { from, to } = range.getDates()
    onRangeChange?.({ fromDate: from, toDate: to })
  }

  // Keep a stable machine timestamp for ordering; labels are presentation only.
  const chartData = useMemo(() => {
    if (!weightHistory?.length) return []

    const byPoint = {}
    weightHistory.forEach(catData => {
      catData.data.forEach(point => {
        const date = new Date(point.timestamp)
        const pointKey = `${date.toISOString()}-${point.visit_id}`
        byPoint[pointKey] = {
          ...(byPoint[pointKey] || {}),
          date: format(date, 'dd MMM yyyy, HH:mm'),
          timestamp: date.getTime(),
          [catData.cat_name]: point.weight_kg,
        }
      })
    })

    return Object.values(byPoint).sort((a, b) => a.timestamp - b.timestamp)
  }, [weightHistory])

  const catNames = weightHistory?.map(c => c.cat_name) || []

  return (
    <div className="card weight-chart-card">
      <div className="flex-between mb-4">
        <div className="card-label">Weight over time</div>
        <div className="chart-range-controls">
          {RANGES.map(range => (
            <button
              key={range.label}
              className={`chart-range-btn ${activeRange === range.label ? 'active' : ''}`}
              onClick={() => handleRange(range)}
              disabled={weightLoading}
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>

      {chartData.length === 0 ? (
        <EmptyState icon={<Icon name="chart" />} message="No weight data yet for this period" compact />
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: 'var(--text-muted)', fontFamily: 'var(--font-body)' }}
              tickLine={false}
              axisLine={{ stroke: 'var(--border)' }}
            />
            <YAxis
              domain={['auto', 'auto']}
              tick={{ fontSize: 10, fill: 'var(--text-muted)', fontFamily: 'var(--font-body)' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={v => `${v}kg`}
            />
            <Tooltip content={<CustomTooltip />} />
            {catNames.length > 1 && (
              <Legend
                wrapperStyle={{ fontSize: '11px', color: 'var(--text-muted)' }}
              />
            )}
            {catNames.map((name, i) => (
              <Line
                key={name}
                type="monotone"
                dataKey={name}
                stroke={CAT_COLORS[i % CAT_COLORS.length]}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, strokeWidth: 0, fill: CAT_COLORS[i % CAT_COLORS.length] }}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
