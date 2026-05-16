import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import WeightChart from './WeightChart'

vi.mock('recharts', () => ({
  CartesianGrid: () => null,
  Legend: () => null,
  Line: () => null,
  LineChart: ({ data }) => (
    <div data-testid="chart-data">{JSON.stringify(data)}</div>
  ),
  ResponsiveContainer: ({ children }) => <div>{children}</div>,
  Tooltip: () => null,
  XAxis: () => null,
  YAxis: () => null,
}))

describe('WeightChart', () => {
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
    expect(data[0].date).toContain('2024')
    expect(data[1].date).toContain('2025')
    expect(data[2].date).toContain('2025')
  })
})
