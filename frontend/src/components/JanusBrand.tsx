import React from 'react';

interface JanusBrandProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showSubtitle?: boolean;
  theme?: 'light' | 'dark';
}

export const JanusSymbol: React.FC<{ size?: number; className?: string }> = ({
  size = 32,
  className = '',
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="JANUS Convergence Symbol"
    >
      <defs>
        {/* Electric Blue gradient: Hypothesis Family A */}
        <linearGradient id="janusTealGrad" x1="4" y1="8" x2="24" y2="24" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#079FF0" />
          <stop offset="100%" stopColor="#0284C7" />
        </linearGradient>

        {/* Pale Cyan gradient: Hypothesis Family B */}
        <linearGradient id="janusAmberGrad" x1="44" y1="40" x2="24" y2="24" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#38BDF8" />
          <stop offset="100%" stopColor="#A8DFF6" />
        </linearGradient>

        {/* Central decision point glow */}
        <filter id="decisionGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="1" stdDeviation="1.5" floodColor="#243640" floodOpacity="0.25" />
        </filter>
      </defs>

      {/* Background circular guide ring */}
      <circle cx="24" cy="24" r="21" stroke="#243640" strokeOpacity="0.1" strokeWidth="1.5" />

      {/* Hypothesis Stream A (Electric blue arc sweeping in from top-left toward center) */}
      <path
        d="M 8 10 C 14 10, 18 16, 22 22"
        stroke="url(#janusTealGrad)"
        strokeWidth="3.2"
        strokeLinecap="round"
      />
      <circle cx="8" cy="10" r="2.5" fill="#079FF0" />

      {/* Hypothesis Stream B (Pale cyan arc sweeping in from bottom-right toward center) */}
      <path
        d="M 40 38 C 34 38, 30 32, 26 26"
        stroke="url(#janusAmberGrad)"
        strokeWidth="3.2"
        strokeLinecap="round"
      />
      <circle cx="40" cy="38" r="2.5" fill="#38BDF8" />

      {/* Decisive Convergence Point: Aperture Diamond */}
      <polygon
        points="24,18 29,24 24,30 19,24"
        fill="#243640"
        filter="url(#decisionGlow)"
      />
      <circle cx="24" cy="24" r="2" fill="#079FF0" />
    </svg>
  );
};

export const JanusBrand: React.FC<JanusBrandProps> = ({
  size = 'md',
  showSubtitle = true,
  theme = 'light',
}) => {
  const pixelSizes = {
    sm: 24,
    md: 32,
    lg: 42,
    xl: 56,
  };

  const titleSizes = {
    sm: '1.05rem',
    md: '1.25rem',
    lg: '1.6rem',
    xl: '2.1rem',
  };

  const isDark = theme === 'dark';

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: size === 'sm' ? '8px' : '12px' }}>
      <JanusSymbol size={pixelSizes[size]} />
      <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.1 }}>
        <span
          style={{
            fontFamily: "'Plus Jakarta Sans', 'Inter', system-ui, sans-serif",
            fontWeight: 800,
            fontSize: titleSizes[size],
            letterSpacing: '-0.02em',
            color: isDark ? '#F5F8F9' : '#243640',
          }}
        >
          JANUS
        </span>
        {showSubtitle && (
          <span
            style={{
              fontSize: size === 'sm' ? '0.62rem' : '0.68rem',
              fontWeight: 700,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              color: isDark ? '#A8DFF6' : '#079FF0',
              marginTop: '1px',
            }}
          >
            Scientific Intelligence
          </span>
        )}
      </div>
    </div>
  );
};
