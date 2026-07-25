/* Lightweight offline phonetic Latin→Kannada transliterator (ITRANS-style).
 * Not exhaustive, but handles most everyday words well enough for input.
 * Non-Latin characters (already-Kannada text) pass through unchanged. */

const VOWELS: Record<string, string> = {
  a: "ಅ", aa: "ಆ", A: "ಆ", i: "ಇ", ii: "ಈ", I: "ಈ", ee: "ಈ",
  u: "ಉ", uu: "ಊ", U: "ಊ", oo: "ಊ", e: "ಎ", E: "ಏ", ai: "ಐ",
  o: "ಒ", O: "ಓ", au: "ಔ", ou: "ಔ",
};
// vowel signs (matras) applied after a consonant
const MATRA: Record<string, string> = {
  a: "", aa: "ಾ", A: "ಾ", i: "ಿ", ii: "ೀ", I: "ೀ", ee: "ೀ",
  u: "ು", uu: "ೂ", U: "ೂ", oo: "ೂ", e: "ೆ", E: "ೇ", ai: "ೈ",
  o: "ೊ", O: "ೋ", au: "ೌ", ou: "ೌ",
};
const CONSONANTS: Record<string, string> = {
  kh: "ಖ", gh: "ಘ", ch: "ಚ", Ch: "ಛ", chh: "ಛ", jh: "ಝ",
  Th: "ಠ", Dh: "ಢ", th: "ಥ", dh: "ಧ", ph: "ಫ", bh: "ಭ",
  sh: "ಶ", Sh: "ಷ", ng: "ಂಗ", ny: "ಞ",
  k: "ಕ", g: "ಗ", j: "ಜ", T: "ಟ", D: "ಡ", N: "ಣ",
  t: "ತ", d: "ದ", n: "ನ", p: "ಪ", b: "ಬ", m: "ಮ",
  y: "ಯ", r: "ರ", l: "ಲ", L: "ಳ", v: "ವ", w: "ವ",
  s: "ಸ", h: "ಹ",
};
const HALANT = "್";

// order matters: try longer keys first
const VKEYS = Object.keys(VOWELS).sort((a, b) => b.length - a.length);
const CKEYS = Object.keys(CONSONANTS).sort((a, b) => b.length - a.length);
const MKEYS = Object.keys(MATRA).sort((a, b) => b.length - a.length);

// High-frequency crime-query words — exact mappings so common phrases read
// perfectly; anything not listed falls back to the rule-based engine below.
const WORD_OVERRIDES: Record<string, string> = {
  namaskara: "ನಮಸ್ಕಾರ", namaskaara: "ನಮಸ್ಕಾರ",
  eshtu: "ಎಷ್ಟು", estu: "ಎಷ್ಟು",
  prakarana: "ಪ್ರಕರಣ", prakaranagalu: "ಪ್ರಕರಣಗಳು", prakaragalu: "ಪ್ರಕರಣಗಳು",
  kole: "ಕೊಲೆ", kolе: "ಕೊಲೆ",
  kallatana: "ಕಳ್ಳತನ", kalatana: "ಕಳ್ಳತನ",
  darode: "ದರೋಡೆ", darode2: "ದರೋಡೆ",
  aparadha: "ಅಪರಾಧ", apradha: "ಅಪರಾಧ",
  bengaluru: "ಬೆಂಗಳೂರು", bengalooru: "ಬೆಂಗಳೂರು",
  mysuru: "ಮೈಸೂರು", mysooru: "ಮೈಸೂರು",
  elli: "ಎಲ್ಲಿ", yaru: "ಯಾರು", yavaga: "ಯಾವಾಗ",
  aropi: "ಆರೋಪಿ", aaropi: "ಆರೋಪಿ",
  cyber: "ಸೈಬರ್", vanchane: "ವಂಚನೆ",
  torisu: "ತೋರಿಸು", torisi: "ತೋರಿಸಿ",
};

function isLatin(ch: string) {
  return /[a-zA-Z]/.test(ch);
}

function transliterateWord(w: string): string {
  let out = "";
  let i = 0;
  while (i < w.length) {
    if (!isLatin(w[i])) { out += w[i]; i++; continue; }
    // try consonant
    let cons = "";
    for (const k of CKEYS) {
      if (w.substr(i, k.length) === k) { cons = k; break; }
    }
    if (cons) {
      i += cons.length;
      // optional following vowel → matra, else halant
      let matra = "";
      let matched = "";
      for (const k of MKEYS) {
        if (w.substr(i, k.length).toLowerCase() === k.toLowerCase() && isVowelStart(w, i, k)) {
          matched = k; matra = MATRA[k]; break;
        }
      }
      if (matched) { out += CONSONANTS[cons] + matra; i += matched.length; }
      else { out += CONSONANTS[cons] + HALANT; }
      continue;
    }
    // try standalone vowel
    let vow = "";
    for (const k of VKEYS) {
      if (w.substr(i, k.length) === k) { vow = k; break; }
    }
    if (vow) { out += VOWELS[vow]; i += vow.length; continue; }
    // passthrough
    out += w[i]; i++;
  }
  return out;
}

function isVowelStart(w: string, i: number, k: string) {
  return w.substr(i, k.length) === k || w.substr(i, k.length).toLowerCase() === k;
}

export function toKannada(text: string): string {
  if (!text) return text;
  // convert token by token, preserving whitespace/punctuation
  return text.replace(/[a-zA-Z]+/g, (m) => {
    const override = WORD_OVERRIDES[m.toLowerCase()];
    return override || transliterateWord(m);
  });
}
