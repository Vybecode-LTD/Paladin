interface BrandmarkProps {
  size?: number;
}

// Constructed shield: flat shoulders, bowed sides converging to an
// optically-overshot point (a mathematically centered tip reads as short —
// it's pushed past the nominal baseline so it *looks* the same weight as the
// flat top). Filled with the site's dual-chromatic gradient, and cut with a
// negative-space signal pulse — the mark reads "protection" (shield) and
// "live intelligence" (the waveform) at once, rather than a generic outline.
export default function Brandmark({ size = 22 }: BrandmarkProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" aria-hidden="true">
      <defs>
        <linearGradient id="pb-shield-grad" x1="8%" y1="4%" x2="88%" y2="100%">
          <stop offset="0%" stopColor="#3989da" />
          <stop offset="55%" stopColor="#0076d1" />
          <stop offset="100%" stopColor="#6044cd" />
        </linearGradient>
        <linearGradient id="pb-sheen" x1="50%" y1="0%" x2="50%" y2="60%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
        </linearGradient>
        <mask id="pb-pulse-mask">
          <rect x="0" y="0" width="64" height="64" fill="#fff" />
          <path
            d="M15 30 H23 L27 20 L33 38 L37 26 L40 30 H49"
            stroke="#000"
            strokeWidth="3.1"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />
        </mask>
      </defs>

      <path
        d="M14 9 H50 C57 9 58 15 58 23 C58 36 51 47 32 59
           C13 47 6 36 6 23 C6 15 7 9 14 9 Z"
        fill="url(#pb-shield-grad)"
        mask="url(#pb-pulse-mask)"
      />
      <path
        d="M14 9 H50 C57 9 58 15 58 23 C58 36 51 47 32 59
           C13 47 6 36 6 23 C6 15 7 9 14 9 Z"
        fill="url(#pb-sheen)"
        mask="url(#pb-pulse-mask)"
      />
    </svg>
  );
}
