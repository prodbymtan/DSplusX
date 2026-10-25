// Inline stroke icons, drawn (not emoji), one consistent 1.6px stroke at 24px.
// Shared across screens so nothing has to reach for emoji.
//
// Decorative by default (aria-hidden). Pass a `title` to give an icon an
// accessible name when it carries meaning on its own.

function Icon({ children, size = 20, title, strokeWidth = 1.6, fillCurrent, ...rest }) {
  return (
    <svg
      className="icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      role={title ? 'img' : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
      {...rest}
    >
      {children}
    </svg>
  )
}

export const PinIcon = (p) => (
  <Icon {...p}>
    <path d="M12 21s-6-5.3-6-10a6 6 0 0 1 12 0c0 4.7-6 10-6 10Z" />
    <circle cx="12" cy="11" r="2.2" />
  </Icon>
)

export const CarIcon = (p) => (
  <Icon {...p}>
    <path d="M5 16V11l1.6-3.6A2 2 0 0 1 8.4 6h7.2a2 2 0 0 1 1.8 1.4L19 11v5" />
    <path d="M4 16h16" />
    <circle cx="7.5" cy="16.5" r="1.4" />
    <circle cx="16.5" cy="16.5" r="1.4" />
  </Icon>
)

export const CardIcon = (p) => (
  <Icon {...p}>
    <rect x="3" y="6" width="18" height="12" rx="2" />
    <path d="M3 10h18M6 14h4" />
  </Icon>
)

export const BellIcon = (p) => (
  <Icon {...p}>
    <path d="M18 8a6 6 0 1 0-12 0c0 6-2 7-2 7h16s-2-1-2-7Z" />
    <path d="M10.5 19a1.8 1.8 0 0 0 3 0" />
  </Icon>
)

export const CheckIcon = (p) => (
  <Icon {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="m8.5 12 2.5 2.5L16 9" />
  </Icon>
)

export const ClockIcon = (p) => (
  <Icon {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7.5V12l3 2" />
  </Icon>
)

export const AlertIcon = (p) => (
  <Icon {...p}>
    <path d="M12 3 2.5 20h19L12 3Z" />
    <path d="M12 10v4" />
    <circle cx="12" cy="17" r="0.4" fill="currentColor" stroke="none" />
  </Icon>
)

export const CalendarIcon = (p) => (
  <Icon {...p}>
    <rect x="4" y="5" width="16" height="16" rx="2" />
    <path d="M4 9h16M9 3v4M15 3v4" />
  </Icon>
)

export const CrossIcon = (p) => (
  <Icon {...p}>
    <rect x="4" y="4" width="16" height="16" rx="3" />
    <path d="M12 8v8M8 12h8" />
  </Icon>
)

export const UploadIcon = (p) => (
  <Icon {...p}>
    <path d="M12 16V4" />
    <path d="m7 9 5-5 5 5" />
    <path d="M5 20h14" />
  </Icon>
)

export const FileIcon = (p) => (
  <Icon {...p}>
    <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8Z" />
    <path d="M14 3v5h5" />
  </Icon>
)

export const WatchIcon = (p) => (
  <Icon {...p}>
    <rect x="7" y="7" width="10" height="10" rx="3" />
    <path d="M9 7l.5-3h5l.5 3M9 17l.5 3h5l.5-3" />
  </Icon>
)

export const HeartIcon = (p) => (
  <Icon {...p}>
    <path d="M12 20s-7-4.6-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.4-7 10-7 10Z" />
  </Icon>
)

export const ActivityIcon = (p) => (
  <Icon {...p}>
    <path d="M3 12h4l2.5 7 5-14L17 12h4" />
  </Icon>
)

export const BrainIcon = (p) => (
  <Icon {...p}>
    <path d="M9 4a2.5 2.5 0 0 0-2.4 3.2A2.5 2.5 0 0 0 5 12a2.5 2.5 0 0 0 1.8 4A2.3 2.3 0 0 0 9 19a2 2 0 0 0 2-2V5a1 1 0 0 0-2 0Z" />
    <path d="M15 4a2.5 2.5 0 0 1 2.4 3.2A2.5 2.5 0 0 1 19 12a2.5 2.5 0 0 1-1.8 4A2.3 2.3 0 0 1 15 19a2 2 0 0 1-2-2" />
  </Icon>
)

export const RunIcon = (p) => (
  <Icon {...p}>
    <circle cx="14" cy="5" r="1.6" />
    <path d="M13 9l-3 2 2 3-1 5M13 9l3 1 2 3M10 11l-3 1-1 3" />
  </Icon>
)

export const DumbbellIcon = (p) => (
  <Icon {...p}>
    <path d="M4 9v6M7 7v10M17 7v10M20 9v6M7 12h10" />
  </Icon>
)

export const ThermometerIcon = (p) => (
  <Icon {...p}>
    <path d="M12 4a2 2 0 0 0-2 2v8a3.5 3.5 0 1 0 4 0V6a2 2 0 0 0-2-2Z" />
    <path d="M12 14V8" />
  </Icon>
)

export const DropIcon = (p) => (
  <Icon {...p}>
    <path d="M12 3s5 5.5 5 9a5 5 0 0 1-10 0c0-3.5 5-9 5-9Z" />
  </Icon>
)

export const TrendIcon = (p) => (
  <Icon {...p}>
    <path d="M4 15l5-5 3 3 6-7" />
    <path d="M18 6h3v3" />
  </Icon>
)

export default Icon
