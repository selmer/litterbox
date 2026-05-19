import { DEFAULT_LANGUAGE, LANGUAGES, translations } from './translations'

export function interpolate(template, params = {}) {
  return Object.entries(params).reduce(
    (value, [key, replacement]) => value.replaceAll(`{${key}}`, replacement),
    template
  )
}

export function createTranslator(language) {
  return (key, params) => {
    const template = translations[language]?.[key] ?? translations[DEFAULT_LANGUAGE]?.[key] ?? key
    return interpolate(template, params)
  }
}

export function normalizeLanguage(language) {
  return LANGUAGES.some(item => item.code === language) ? language : DEFAULT_LANGUAGE
}
