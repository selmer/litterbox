import { useState, useMemo } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import { format } from 'date-fns'
import { enGB, nl } from 'date-fns/locale'
import Icon from './Icon'
import { EmptyState } from './ui'
import { CHART_RANGE_STORAGE_KEY, getInitialRangeLabel, RANGES } from '../utils/chartRanges'
import { useLanguage } from '../i18n/LanguageContext'

function getTickCount(rangeLabel) {
  return { '1W': 4, '1M': 5, '3M': 6, '1Y': 7, All: 6 }[rangeLabel] || 6
}

function getMinTickGap(rangeLabel) {
  return rangeLabel === '1W' ? 28 : 42
}

function formatDateTick(timestamp, rangeLabel, dateLocale) {
  const date = new Date(timestamp)
  if (rangeLabel === '1W') return format(date, 'EEE', { locale: dateLocale })
  if (rangeLabel === '1M') return format(date, 'dd MMM', { locale: dateLocale })
  if (rangeLabel === '3M') return format(date, 'MMM d', { locale: dateLocale })
  if (rangeLabel === '1Y') return format(date, 'MMM yy', { locale: dateLocale })
  return format(date, 'yyyy', { locale: dateLocale })
}

function formatKg(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return ''
  return `${number.toFixed(1)} kg`
}

// One colour per cat — accent for first, then a softer second
const CAT_COLORS = ['var(--chart-line)', 'var(--success)', '#38BDF8', '#F59E0B']

function CustomTooltip({ active, payload, label, t, dateLocale }) {
  const rows = payload?.filter(entry => Number.isFinite(Number(entry.value))) || []
  if (!active || rows.length === 0) return null
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip__date">{format(new Date(label), 'dd MMM yyyy, HH:mm', { locale: dateLocale })}</div>
      {rows.map((entry) => (
        <div key={entry.name} className="chart-tooltip__row">
          <span style={{ color: entry.color }}>{entry.name}</span>
          <span>
            {Number(entry.value).toFixed(3)} kg
            {entry.payload?.[`${entry.name}VisitId`] && ` · ${t('chart.visitId', { id: entry.payload[`${entry.name}VisitId`] })}`}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function WeightChart({ weightHistory, onRangeChange, weightLoading = false }) {
  const { language, t } = useLanguage()
  const dateLocale = language === 'nl' ? nl : enGB
  const [activeRange, setActiveRange] = useState(getInitialRangeLabel)

  function handleRange(range) {
    setActiveRange(range.label)
    window.localStorage?.setItem(CHART_RANGE_STORAGE_KEY, range.label)
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
          date: format(date, 'dd MMM yyyy, HH:mm', { locale: dateLocale }),
          timestamp: date.getTime(),
          [catData.cat_name]: point.weight_kg,
          [`${catData.cat_name}VisitId`]: point.visit_id,
        }
      })
    })

    return Object.values(byPoint).sort((a, b) => a.timestamp - b.timestamp)
  }, [weightHistory, dateLocale])

  const catNames = weightHistory?.map(c => c.cat_name) || []

  return (
    <div className="card weight-chart-card">
      <div className="flex-between mb-4">
        <div className="card-label">{t('chart.weightOverTime')}</div>
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
        <EmptyState icon={<Icon name="chart" />} message={t('chart.noWeightData')} compact />
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={chartData} margin={{ top: 4, right: 10, bottom: 0, left: -8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
            <XAxis
              dataKey="timestamp"
              type="number"
              domain={['dataMin', 'dataMax']}
              tick={{ fontSize: 10, fill: 'var(--text-muted)', fontFamily: 'var(--font-body)' }}
              tickLine={false}
              axisLine={{ stroke: 'var(--border)' }}
              tickCount={getTickCount(activeRange)}
              minTickGap={getMinTickGap(activeRange)}
              interval="preserveStartEnd"
              tickFormatter={(value) => formatDateTick(value, activeRange, dateLocale)}
            />
            <YAxis
              domain={['auto', 'auto']}
              tick={{ fontSize: 10, fill: 'var(--text-muted)', fontFamily: 'var(--font-body)' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={formatKg}
            />
            <Tooltip content={<CustomTooltip t={t} dateLocale={dateLocale} />} />
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
