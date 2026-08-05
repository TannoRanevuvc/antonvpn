interface PortalMarkProps {
  size?: number;
  color?: string;
}

export function PortalMark({ size = 32, color = "currentColor" }: PortalMarkProps) {
  // Two arcs forming an open portal with an 'A' shape in negative space
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      {/* Left arc */}
      <path
        d="M8 28 C8 28 4 22 4 16 C4 9.373 9.373 4 16 4"
        stroke={color}
        strokeWidth="2.5"
        strokeLinecap="round"
        fill="none"
      />
      {/* Right arc */}
      <path
        d="M24 28 C24 28 28 22 28 16 C28 9.373 22.627 4 16 4"
        stroke={color}
        strokeWidth="2.5"
        strokeLinecap="round"
        fill="none"
      />
      {/* Crossbar of the A in negative space */}
      <path
        d="M11 20 L21 20"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  );
}
