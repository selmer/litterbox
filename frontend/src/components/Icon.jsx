const ICON_PATHS = {
  cat: (
    <>
      <path d="M4 10.5 5.4 4l4.1 3h5l4.1-3L20 10.5" />
      <path d="M5 10.5c0 5.2 2.7 8.5 7 8.5s7-3.3 7-8.5" />
      <path d="M9 13h.01" />
      <path d="M15 13h.01" />
      <path d="M11 16h2" />
    </>
  ),
  dashboard: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="5" rx="1.5" />
      <rect x="14" y="12" width="7" height="9" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
    </>
  ),
  visits: (
    <>
      <path d="M8 3v4" />
      <path d="M16 3v4" />
      <rect x="4" y="5" width="16" height="16" rx="2" />
      <path d="M4 10h16" />
      <path d="M8 14h3" />
      <path d="M8 17h6" />
    </>
  ),
  moon: (
    <path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a7 7 0 1 0 10.5 10.5Z" />
  ),
  sun: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2" />
      <path d="M12 20v2" />
      <path d="m4.93 4.93 1.41 1.41" />
      <path d="m17.66 17.66 1.41 1.41" />
      <path d="M2 12h2" />
      <path d="M20 12h2" />
      <path d="m6.34 17.66-1.41 1.41" />
      <path d="m19.07 4.93-1.41 1.41" />
    </>
  ),
  scale: (
    <>
      <path d="M6 19h12" />
      <rect x="5" y="4" width="14" height="12" rx="3" />
      <path d="M9 8c1.8-1.3 4.2-1.3 6 0" />
      <path d="m12 9 2-2" />
    </>
  ),
  timer: (
    <>
      <path d="M10 2h4" />
      <path d="M12 14V9" />
      <path d="M12 22a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z" />
      <path d="m17 7 1.5-1.5" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  activity: (
    <>
      <path d="M4 12h3l2-6 4 12 2-6h5" />
    </>
  ),
  alert: (
    <>
      <path d="m12 3 10 18H2L12 3Z" />
      <path d="M12 9v5" />
      <path d="M12 17h.01" />
    </>
  ),
  chart: (
    <>
      <path d="M4 19V5" />
      <path d="M4 19h16" />
      <path d="m7 15 4-4 3 2 5-7" />
    </>
  ),
  clean: (
    <>
      <path d="M7 21h10" />
      <path d="M9 21V9" />
      <path d="M15 21V9" />
      <path d="M8 9h8l-1-5H9L8 9Z" />
      <path d="M10 13h4" />
      <path d="M10 17h4" />
    </>
  ),
  download: (
    <>
      <path d="M12 3v12" />
      <path d="m7 10 5 5 5-5" />
      <path d="M5 21h14" />
    </>
  ),
  upload: (
    <>
      <path d="M12 21V9" />
      <path d="m7 14 5-5 5 5" />
      <path d="M5 3h14" />
    </>
  ),
  restore: (
    <>
      <path d="M3 12a9 9 0 1 0 3-6.7" />
      <path d="M3 4v6h6" />
      <path d="M12 8v5l3 2" />
    </>
  ),
  moreHorizontal: (
    <>
      <circle cx="5" cy="12" r="1" />
      <circle cx="12" cy="12" r="1" />
      <circle cx="19" cy="12" r="1" />
    </>
  ),
  close: (
    <>
      <path d="M18 6 6 18" />
      <path d="m6 6 12 12" />
    </>
  ),
  archive: (
    <>
      <rect x="4" y="4" width="16" height="5" rx="1" />
      <path d="M6 9v10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V9" />
      <path d="M10 13h4" />
    </>
  ),
}

export default function Icon({ name, size = 18, className = '', title }) {
  const paths = ICON_PATHS[name]
  if (!paths) return null

  return (
    <svg
      className={`app-icon ${className}`.trim()}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={title ? undefined : 'true'}
      role={title ? 'img' : undefined}
    >
      {title && <title>{title}</title>}
      {paths}
    </svg>
  )
}

export function CatAvatarIcon({ className = '' }) {
  return <Icon name="cat" size={28} className={`cat-avatar-icon ${className}`.trim()} />
}
