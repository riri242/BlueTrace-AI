export function HeroIllustration() {
  return (
    <svg
      aria-label="Abstract coastal research illustration"
      className="h-auto w-full"
      role="img"
      viewBox="0 0 520 420"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="seaGradient" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stopColor="#e6f5fb" />
          <stop offset="52%" stopColor="#c7e8f4" />
          <stop offset="100%" stopColor="#f8fbff" />
        </linearGradient>
        <linearGradient id="coastGradient" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stopColor="#d7eef6" />
          <stop offset="100%" stopColor="#f4fafc" />
        </linearGradient>
      </defs>

      <rect fill="url(#seaGradient)" height="420" rx="36" width="520" />
      <path
        d="M80 364C128 308 112 246 164 226C216 206 255 252 306 218C357 184 333 116 397 84C439 63 478 82 520 116V420H80V364Z"
        fill="url(#coastGradient)"
      />
      <path
        d="M0 270C74 226 134 244 195 210C256 176 290 120 364 120C419 120 471 148 520 190"
        fill="none"
        stroke="#1f8ab5"
        strokeLinecap="round"
        strokeWidth="3"
      />
      <path
        d="M56 118C118 92 170 92 232 118C294 144 346 144 408 118"
        fill="none"
        opacity="0.7"
        stroke="#8ac8dd"
        strokeLinecap="round"
        strokeWidth="4"
      />
      <path
        d="M66 162C128 136 180 136 242 162C304 188 356 188 418 162"
        fill="none"
        opacity="0.45"
        stroke="#8ac8dd"
        strokeLinecap="round"
        strokeWidth="4"
      />

      <g opacity="0.55" stroke="#9bb6c9" strokeWidth="1">
        <path d="M80 56V344" />
        <path d="M144 40V360" />
        <path d="M208 48V352" />
        <path d="M272 40V360" />
        <path d="M336 48V352" />
        <path d="M400 56V344" />
        <path d="M48 96H472" />
        <path d="M40 160H482" />
        <path d="M56 224H490" />
        <path d="M72 288H470" />
      </g>

      <circle cx="198" cy="208" fill="#ffffff" r="30" />
      <circle cx="198" cy="208" fill="none" r="48" stroke="#1f8ab5" />
      <circle cx="198" cy="208" fill="#146f94" r="9" />

      <g fill="none" strokeLinecap="round" strokeWidth="4">
        <path d="M330 250L372 236L404 260" stroke="#146f94" />
        <path d="M330 278L374 264L420 292" stroke="#69b7d4" />
      </g>

      <circle cx="390" cy="96" fill="#ffffff" r="14" />
      <circle cx="426" cy="118" fill="#ffffff" opacity="0.75" r="8" />
      <circle cx="112" cy="294" fill="#146f94" opacity="0.18" r="20" />
      <circle cx="438" cy="310" fill="#1f8ab5" opacity="0.16" r="26" />
    </svg>
  );
}

