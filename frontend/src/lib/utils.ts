export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ')
}

export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat('en-GB', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(new Date(iso))
}

export function formatDateTime(iso: string): string {
  return new Intl.DateTimeFormat('en-GB', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))
}

export function isExpiringSoon(endDateIso: string, thresholdDays = 30): boolean {
  const diff = new Date(endDateIso).getTime() - Date.now()
  return diff > 0 && diff < thresholdDays * 86_400_000
}

export function isExpired(endDateIso: string): boolean {
  return new Date(endDateIso).getTime() < Date.now()
}
