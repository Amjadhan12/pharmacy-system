const DIGIT_RANGES = [
  { start: 0x0660, end: 0x0669 },
  { start: 0x06f0, end: 0x06f9 },
]

export function normalizeDigits(value: string): string {
  return Array.from(value, (character) => {
    const code = character.codePointAt(0)
    if (code === undefined) return character
    const range = DIGIT_RANGES.find(
      ({ start, end }) => code >= start && code <= end,
    )
    return range ? String(code - range.start) : character
  }).join('')
}
