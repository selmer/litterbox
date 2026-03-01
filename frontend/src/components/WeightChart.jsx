import { useState, useMemo } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import { subDays, subMonths, subYears, format } from 'date-fns'

const RANGES = [
  { label: '1W', getDates: () => ({ from: subDays(new Date(), 7),   to: new Date() }) },
  { label: '1M', getDates: () => ({ from: subMonths(new Date(), 1), to: new Date() }) },
  { label: '3M', getDates: () => ({ from: subMonths(new Date(), 3), to: new Date() }) },
  { label: '1Y', getDates: () => ({ from: subYears(new Date(), 1),  to: new Date() }) },
  { label: 'All', getDates: () => ({ from: new Date(0),             to: new Date() }) },
]

// One colour per cat — accent for first, then a softer second
const CAT_COLORS = ['#e07b54', '#7c6af7', '#22c55e', '#f59e0b']

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

export default function WeightChart({ weightHistory, onRangeChange }) {
  const [activeRange, setActiveRange] = useState('1Y')

  function handleRange(range) {
    setActiveRange(range.label)
    const { from, to } = range.getDates()
    onRangeChange?.({ fromDate: from, toDate: to })
  }

  // Merge all cats' data points into a single array keyed by date string
  const chartData = useMemo(() => {
    if (!weightHistory?.length) return []

    const byDate = {}
    weightHistory.forEach(catData => {
      catData.data.forEach(point => {
        const dateKey = format(new Date(point.timestamp), 'dd MMM')
        if (!byDate[dateKey]) byDate[dateKey] = { date: dateKey }
        byDate[dateKey][catData.cat_name] = point.weight_kg
      })
    })

    return Object.values(byDate).sort((a, b) =>
      new Date(a.date) - new Date(b.date)
    )
  }, [weightHistory])

  const catNames = weightHistory?.map(c => c.cat_name) || []

  return (
    <div className="card">
      <div className="flex-between mb-4">
        <div className="card-label">Weight over time</div>
        <div className="chart-range-controls">
          {RANGES.map(range => (
            <button
              key={range.label}
              className={`chart-range-btn ${activeRange === range.label ? 'active' : ''}`}
              onClick={() => handleRange(range)}
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>

      {chartData.length === 0 ? (
        <div className="empty-state" style={{ padding: '40px 0' }}>
          <div className="empty-icon">📈</div>
          <p>No weight data yet for this period</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
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
                activeDot={{ r: 4, strokeWidth: 0 }}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
