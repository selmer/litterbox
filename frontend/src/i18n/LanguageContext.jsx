import { useEffect, useMemo, useState } from 'react'
import { LanguageContext } from './languageContextObject'
import { createTranslator, normalizeLanguage } from './languageUtils'
import { DEFAULT_LANGUAGE, LANGUAGES, LANGUAGE_STORAGE_KEY } from './translations'

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
