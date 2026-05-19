import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { DEFAULT_LANGUAGE, LANGUAGES, LANGUAGE_STORAGE_KEY, translations } from './translations'

const LanguageContext = createContext(null)

function interpolate(template, params = {}) {
  return Object.entries(params).reduce(
    (value, [key, replacement]) => value.replaceAll(`{${key}}`, replacement),
    template
  )
}

function createTranslator(language) {
  return (key, params) => {
    const template = translations[language]?.[key] ?? translations[DEFAULT_LANGUAGE]?.[key] ?? key
    return interpolate(template, params)
  }
}

function normalizeLanguage(language) {
  return LANGUAGES.some(item => item.code === language) ? language : DEFAULT_LANGUAGE
}

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => {
    if (typeof window === 'undefined') return DEFAULT_LANGUAGE
    return normalizeLanguage(window.localStorage?.getItem(LANGUAGE_STORAGE_KEY))
  })

  useEffect(() => {
    document.documentElement.setAttribute('lang', language)
    window.localStorage?.setItem(LANGUAGE_STORAGE_KEY, language)
  }, [language])

  const value = useMemo(() => {
    const languageMeta = LANGUAGES.find(item => item.code === language) || LANGUAGES[0]
    const t = createTranslator(language)
    return {
      language,
      locale: languageMeta.locale,
      languages: LANGUAGES,
      setLanguage: nextLanguage => setLanguageState(normalizeLanguage(nextLanguage)),
      t,
    }
  }, [language])

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (!context) {
    const fallback = LANGUAGES.find(item => item.code === DEFAULT_LANGUAGE)
    return {
      language: DEFAULT_LANGUAGE,
      locale: fallback.locale,
      languages: LANGUAGES,
      setLanguage: () => {},
      t: createTranslator(DEFAULT_LANGUAGE),
    }
  }
  return context
}
