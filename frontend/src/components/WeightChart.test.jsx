import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { cloneElement } from 'react'
import WeightChart from './WeightChart'
import { CHART_RANGE_STORAGE_KEY } from '../utils/chartRanges'

vi.mock('recharts', () => ({
  CartesianGrid: () => null,
  Legend: () => null,
  Line: () => null,
  LineChart: ({ data, children }) => (
    <div>
      <div data-testid="chart-data">{JSON.stringify(data)}</div>
      {children}
    </div>
  ),
  ResponsiveContainer: ({ children }) => <div>{children}</div>,
  Tooltip: ({ content }) => content ? (
    <div data-testid="tooltip">
      {cloneElement(content, {
        active: true,
        label: new Date('2025-01-01T10:00:00Z').getTime(),
        payload: [
          {
            name: 'Mochi',
            value: 4.1,
            color: 'red',
            payload: {
              MochiRecordedWeight: 4.2,
              MochiVisitId: 2,
            },
          },
        ],
      })}
    </div>
  ) : null,
  XAxis: (props) => (
    <div
      data-testid="x-axis"
      data-tick-count={props.tickCount}
      data-min-tick-gap={props.minTickGap}
      data-sample-tick={props.tickFormatter?.(new Date('2025-01-01T00:00:00Z').getTime())}
    />
  ),
  YAxis: (props) => (
    <div data-testid="y-axis" data-sample-tick={props.tickFormatter?.(3.76)} />
  ),
}))

function chartRows() {
  return JSON.parse(screen.getByTestId('chart-data').textContent)
}

function directionReversals(values) {
  const directions = values
    .map((value, index) => {
      if (index === 0) return 0
      const delta = value - values[index - 1]
      if (Math.abs(delta) < 0.001) return 0
      return delta > 0 ? 1 : -1
    })
    .filter(Boolean)

  return directions.reduce((count, direction, index) => {
    if (index === 0) return count
    return direction !== directions[index - 1] ? count + 1 : count
  }, 0)
}

describe('WeightChart', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('keeps cross-year and same-day points distinct and sorted', () => {
    render(
      <WeightChart
        weightHistory={[
          {
            cat_id: 1,
            cat_name: 'Mochi',
            data: [
              { timestamp: '2025-01-01T10:00:00Z', weight_kg: 4.2, visit_id: 2 },
              { timestamp: '2024-01-01T10:00:00Z', weight_kg: 4.0, visit_id: 1 },
              { timestamp: '2025-01-01T12:00:00Z', weight_kg: 4.3, visit_id: 3 },
            ],
          },
        ]}
      />
    )

    const data = chartRows()
    expect(data).toHaveLength(3)
    expect(data.map(point => point.Mochi)).toEqual([4.0, 4.2, 4.3])
    expect(data.map(point => point.MochiRecordedWeight)).toEqual([4.0, 4.2, 4.3])
    expect(data.map(point => point.MochiVisitId)).toEqual([1, 2, 3])
    expect(data[0].date).toContain('2024')
    expect(data[1].date).toContain('2025')
    expect(data[2].date).toContain('2025')
  })

  it('persists the selected range and restores it on next render', () => {
    const onRangeChange = vi.fn()
    const { unmount } = render(
      <WeightChart
        weightHistory={[
          {
            cat_id: 1,
            cat_name: 'Mochi',
            data: [{ timestamp: '2025-01-01T10:00:00Z', weight_kg: 4.2, visit_id: 1 }],
          },
        ]}
        onRangeChange={onRangeChange}
      />
    )

    fireEvent.click(screen.getByRole('button', { name: 'All' }))

    expect(window.localStorage.getItem(CHART_RANGE_STORAGE_KEY)).toBe('All')
    expect(onRangeChange).toHaveBeenCalledWith(expect.objectContaining({
      fromDate: new Date(0),
    }))

    unmount()
    render(<WeightChart weightHistory={[]} />)

    expect(screen.getByRole('button', { name: 'All' })).toHaveClass('active')
  })

  it('uses readable chart tick formatting', () => {
    render(
      <WeightChart
        weightHistory={[
          {
            cat_id: 1,
            cat_name: 'Mochi',
            data: [{ timestamp: '2025-01-01T10:00:00Z', weight_kg: 4.2, visit_id: 1 }],
          },
        ]}
      />
    )

    expect(screen.getByTestId('x-axis')).toHaveAttribute('data-tick-count', '7')
    expect(screen.getByTestId('x-axis')).toHaveAttribute('data-min-tick-gap', '42')
    expect(screen.getByTestId('y-axis')).toHaveAttribute('data-sample-tick', '3.8 kg')
  })

  it('smooths noisy same-cat data and reduces direction reversals', () => {
    const rawWeights = [4.0, 4.2, 4.0, 4.2, 4.0, 4.2, 4.0, 4.2, 4.0, 4.2]
    render(
      <WeightChart
        weightHistory={[
          {
            cat_id: 1,
            cat_name: 'Mochi',
            data: rawWeights.map((weight, index) => ({
              timestamp: `2025-01-${String(index + 1).padStart(2, '0')}T10:00:00Z`,
              weight_kg: weight,
              visit_id: index + 1,
            })),
          },
        ]}
      />
    )

    const displayedWeights = chartRows().map(point => point.Mochi)
    expect(directionReversals(displayedWeights)).toBeLessThanOrEqual(directionReversals(rawWeights) / 2)
  })

  it('preserves sustained weight change direction over at least seven days', () => {
    render(
      <WeightChart
        weightHistory={[
          {
            cat_id: 1,
            cat_name: 'Mochi',
            data: [4.0, 4.04, 4.08, 4.12, 4.16, 4.2, 4.24, 4.28].map((weight, index) => ({
              timestamp: `2025-02-${String(index + 1).padStart(2, '0')}T10:00:00Z`,
              weight_kg: weight,
              visit_id: index + 1,
            })),
          },
        ]}
      />
    )

    const displayedWeights = chartRows().map(point => point.Mochi)
    expect(displayedWeights.at(-1)).toBeGreaterThan(displayedWeights[0])
  })

  it('smooths each cat independently', () => {
    render(
      <WeightChart
        weightHistory={[
          {
            cat_id: 1,
            cat_name: 'Mochi',
            data: [4.0, 4.2, 4.0, 4.2, 4.0].map((weight, index) => ({
              timestamp: `2025-03-${String(index + 1).padStart(2, '0')}T10:00:00Z`,
              weight_kg: weight,
              visit_id: index + 1,
            })),
          },
          {
            cat_id: 2,
            cat_name: 'Luna',
            data: [6.0, 6.0, 6.0, 6.0, 6.0].map((weight, index) => ({
              timestamp: `2025-03-${String(index + 1).padStart(2, '0')}T11:00:00Z`,
              weight_kg: weight,
              visit_id: index + 101,
            })),
          },
        ]}
      />
    )

    const rows = chartRows()
    expect(rows.filter(point => point.Luna != null).map(point => point.Luna)).toEqual([6.0, 6.0, 6.0, 6.0, 6.0])
    expect(rows.filter(point => point.Mochi != null).some(point => point.Mochi !== point.MochiRecordedWeight)).toBe(true)
  })

  it('retains recorded weight and visit context for smoothed points', () => {
    render(
      <WeightChart
        weightHistory={[
          {
            cat_id: 1,
            cat_name: 'Mochi',
            data: [
              { timestamp: '2025-04-01T10:00:00Z', weight_kg: 4.0, visit_id: 1, weight_confidence: 'normal' },
              { timestamp: '2025-04-02T10:00:00Z', weight_kg: 4.2, visit_id: 2, weight_confidence: 'normal' },
              { timestamp: '2025-04-03T10:00:00Z', weight_kg: 4.0, visit_id: 3, weight_confidence: 'normal' },
            ],
          },
        ]}
      />
    )

    const smoothedPoint = chartRows()[1]
    expect(smoothedPoint.Mochi).toBeCloseTo(4.1)
    expect(smoothedPoint.MochiRecordedWeight).toBe(4.2)
    expect(smoothedPoint.MochiVisitId).toBe(2)
    expect(smoothedPoint.MochiWeightConfidence).toBe('normal')
  })

  it('shows recorded weight context in tooltip copy when smoothing changes the displayed value', () => {
    render(
      <WeightChart
        weightHistory={[
          {
            cat_id: 1,
            cat_name: 'Mochi',
            data: [
              { timestamp: '2025-01-01T10:00:00Z', weight_kg: 4.0, visit_id: 1 },
              { timestamp: '2025-01-02T10:00:00Z', weight_kg: 4.2, visit_id: 2 },
              { timestamp: '2025-01-03T10:00:00Z', weight_kg: 4.0, visit_id: 3 },
            ],
          },
        ]}
      />
    )

    expect(screen.getByTestId('tooltip')).toHaveTextContent('4.100 kg')
    expect(screen.getByTestId('tooltip')).toHaveTextContent('recorded 4.200 kg')
    expect(screen.getByTestId('tooltip')).toHaveTextContent('Visit #2')
  })

  it('does not smooth one-point and two-point histories', () => {
    render(
      <WeightChart
        weightHistory={[
          {
            cat_id: 1,
            cat_name: 'Mochi',
            data: [
              { timestamp: '2025-05-01T10:00:00Z', weight_kg: 4.0, visit_id: 1 },
              { timestamp: '2025-05-02T10:00:00Z', weight_kg: 4.2, visit_id: 2 },
            ],
          },
        ]}
      />
    )

    const rows = chartRows()
    expect(rows.map(point => point.Mochi)).toEqual([4.0, 4.2])
    expect(rows.map(point => point.MochiRecordedWeight)).toEqual([4.0, 4.2])
  })

  it('handles gaps, same-day repeated readings, and invalid weights without invented points', () => {
    render(
      <WeightChart
        weightHistory={[
          {
            cat_id: 1,
            cat_name: 'Mochi',
            data: [
              { timestamp: '2025-06-01T10:00:00Z', weight_kg: 4.0, visit_id: 1 },
              { timestamp: '2025-06-01T12:00:00Z', weight_kg: 4.2, visit_id: 2 },
              { timestamp: '2025-07-10T10:00:00Z', weight_kg: 4.4, visit_id: 3 },
              { timestamp: '2025-07-11T10:00:00Z', weight_kg: Number.NaN, visit_id: 4 },
              { timestamp: 'not-a-date', weight_kg: 4.6, visit_id: 5 },
            ],
          },
        ]}
      />
    )

    const rows = chartRows()
    expect(rows).toHaveLength(3)
    expect(rows.map(point => point.MochiVisitId)).toEqual([1, 2, 3])
    expect(rows.map(point => point.Mochi)).toEqual([4.0, 4.2, 4.4])
  })

})
