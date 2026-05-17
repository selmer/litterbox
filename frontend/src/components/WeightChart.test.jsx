import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
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
  Tooltip: () => null,
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

    const data = JSON.parse(screen.getByTestId('chart-data').textContent)
    expect(data).toHaveLength(3)
    expect(data.map(point => point.Mochi)).toEqual([4.0, 4.2, 4.3])
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

})
