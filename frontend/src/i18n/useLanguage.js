import { useContext } from 'react'
import { LanguageContext } from './languageContextObject'
import { DEFAULT_LANGUAGE, LANGUAGES } from './translations'
import { createTranslator } from './languageUtils'

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
