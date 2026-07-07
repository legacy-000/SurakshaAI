import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Language = 'en' | 'kn';

interface LanguageContextType {
  lang: Language;
  toggleLang: () => void;
  t: (en: string, kn: string) => string;
}

const LanguageContext = createContext<LanguageContextType>({
  lang: 'en',
  toggleLang: () => {},
  t: (en: string) => en,
});

export const LanguageProvider = ({ children }: { children: ReactNode }) => {
  const [lang, setLang] = useState<Language>(() => {
    return (localStorage.getItem('lang') as Language) || 'en';
  });

  useEffect(() => {
    localStorage.setItem('lang', lang);
  }, [lang]);

  const toggleLang = () => setLang(l => (l === 'en' ? 'kn' : 'en'));
  const t = (en: string, kn: string) => (lang === 'kn' ? kn : en);

  return (
    <LanguageContext.Provider value={{ lang, toggleLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => useContext(LanguageContext);
