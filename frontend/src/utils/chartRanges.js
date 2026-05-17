import { subDays, subMonths, subYears } from 'date-fns'

export const CHART_RANGE_STORAGE_KEY = 'litterbox.weightChart.range'

export const RANGES = [
  { label: '1W', getDates: () => ({ from: subDays(new Date(), 7), to: new Date() }) },
  { label: '1M', getDates: () => ({ from: subMonths(new Date(), 1), to: new Date() }) },
  { label: '3M', getDates: () => ({ from: subMonths(new Date(), 3), to: new Date() }) },
  { label: '1Y', getDates: () => ({ from: subYears(new Date(), 1), to: new Date() }) },
  { label: 'All', getDates: () => ({ from: new Date(0), to: new Date() }) },
]

export function getRangeDates(label) {
  return (RANGES.find(range => range.label === label) || RANGES[3]).getDates()
}

export function getInitialRangeLabel() {
  if (typeof window === 'undefined') return '1Y'
  const stored = window.localStorage?.getItem(CHART_RANGE_STORAGE_KEY)
  return RANGES.some(range => range.label === stored) ? stored : '1Y'
}
