'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { Locale, getTranslation, t as translate } from './i18n'

interface LocaleContextType {
  locale: Locale
  setLocale: (locale: Locale) => void
  t: (path: string) => string
  translations: ReturnType<typeof getTranslation>
}

const LocaleContext = createContext<LocaleContextType | undefined>(undefined)

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>('ru')

  useEffect(() => {
    // Load saved language from localStorage
    const savedLocale = localStorage.getItem('tracy_locale') as Locale | null
    if (savedLocale && (savedLocale === 'ru' || savedLocale === 'en')) {
      setLocaleState(savedLocale)
      // Update HTML lang attribute
      if (typeof document !== 'undefined') {
        document.documentElement.lang = savedLocale
      }
    }
  }, [])

  const setLocale = (newLocale: Locale) => {
    setLocaleState(newLocale)
    localStorage.setItem('tracy_locale', newLocale)
    if (typeof document !== 'undefined') {
      document.documentElement.lang = newLocale
    }
  }

  const t = (path: string) => translate(locale, path)
  const translations = getTranslation(locale)

  return (
    <LocaleContext.Provider value={{ locale, setLocale, t, translations }}>
      {children}
    </LocaleContext.Provider>
  )
}

export function useLocale() {
  const context = useContext(LocaleContext)
  if (!context) {
    throw new Error('useLocale must be used within LocaleProvider')
  }
  return context
}



