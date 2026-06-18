function formatWeight(value, locale) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return null
  const formatted = new Intl.NumberFormat(locale, {
    minimumFractionDigits: 1,
    maximumFractionDigits: 3,
  }).format(Number(value))
  return `${formatted} kg`
}

function formatNumber(value, locale, digits = 1) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return null
  return new Intl.NumberFormat(locale, {
    maximumFractionDigits: digits,
  }).format(Number(value))
}

function translateWindow(window, t) {
  if (window === '1 month') return t('healthSignal.window.oneMonth')
  if (window === '3 months') return t('healthSignal.window.threeMonths')
  if (window === 'last 7 days') return t('healthSignal.window.lastSevenDays')
  if (window === 'previous 21 days') return t('healthSignal.window.previousTwentyOneDays')
  return window
}

export function formatHealthSignal(signal, t, locale) {
  const metadata = signal.metadata || {}

  if (signal.type === 'weight_up' || signal.type === 'weight_down') {
    const window = translateWindow(metadata.comparison_window, t)
    const current = formatWeight(metadata.current_weight_kg, locale)
    const baseline = formatWeight(metadata.baseline_weight_kg, locale)

    return {
      message: t(`healthSignal.${signal.type}`, { window }),
      detail: current && baseline
        ? t('healthSignal.weightDetail', { current, baseline, window })
        : signal.detail,
    }
  }

  if (signal.type === 'visits_higher' || signal.type === 'visits_lower') {
    const current = metadata.current_visits
    const baseline = formatNumber(metadata.baseline_weekly_visits, locale)

    return {
      message: t(`healthSignal.${signal.type}`),
      detail: current !== undefined && baseline
        ? t('healthSignal.visitsDetail', { current, baseline })
        : signal.detail,
    }
  }

  if (signal.type === 'unidentified_visits') {
    const count = metadata.unidentified_visits
    return {
      message: t('healthSignal.unidentified_visits'),
      detail: count !== undefined
        ? t('healthSignal.unidentifiedDetail', { count })
        : signal.detail,
    }
  }

  if (signal.type === 'stale_device_data') {
    return {
      message: t('healthSignal.stale_device_data'),
      detail: metadata.last_error || signal.detail || t('healthSignal.staleDeviceDetail'),
    }
  }

  return {
    message: signal.message,
    detail: signal.detail,
  }
}
