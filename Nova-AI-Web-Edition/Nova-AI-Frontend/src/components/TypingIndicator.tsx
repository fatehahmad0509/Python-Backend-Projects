// src/components/TypingIndicator.tsx
import React from 'react';

const sharedStyles = `
  @keyframes spinArc { to { transform: rotate(360deg); } }
  @keyframes breathe {
    0%, 100% { box-shadow: 0 0 0 0 rgba(139,92,246,0); background: rgba(139,92,246,0.08); border-color: rgba(139,92,246,0.25); }
    50% { box-shadow: 0 0 14px 3px rgba(139,92,246,0.25); background: rgba(139,92,246,0.15); border-color: rgba(139,92,246,0.5); }
  }
  @keyframes breatheIcon {
    0%, 100% { opacity: 0.6; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.12); }
  }
  @keyframes breatheText {
    0%, 100% { opacity: 0.7; }
    50% { opacity: 1; }
  }
  @keyframes typingBounce {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
    30% { transform: translateY(-6px); opacity: 1; }
  }
`;

function SpinningArc() {
  return (
    <div className="relative h-5 w-5 shrink-0">
      <div className="absolute inset-0 rounded-full border-[2.5px] border-accent/25" />
      <div className="absolute inset-0 animate-[spinArc_1s_linear_infinite] rounded-full border-[2.5px] border-transparent border-r-accent-light border-t-accent-light" />
      <div className="absolute inset-1 animate-[spinArc_0.7s_linear_infinite_reverse] rounded-full border-[2px] border-transparent border-b-accent-light" />
    </div>
  );
}

function IndicatorBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-w-[180px] animate-[breathe_2s_ease-in-out_infinite] items-center gap-[10px] rounded-[14px] border border-accent/25 bg-accent/10 px-3.5 py-2.5">
      <style>{sharedStyles}</style>
      {children}
    </div>
  );
}

export function WebSearchIndicator() {
  return (
    <IndicatorBox>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
        className="shrink-0 animate-[breatheIcon_2s_ease-in-out_infinite] text-accent-light">
        <circle cx="12" cy="12" r="10"/>
        <line x1="2" y1="12" x2="22" y2="12"/>
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
      </svg>
      <span className="animate-[breatheText_2s_ease-in-out_infinite] text-xs font-medium tracking-wide text-accent-light">
        Searching the Web...
      </span>
    </IndicatorBox>
  );
}

export function ThinkingIndicator() {
  return (
    <IndicatorBox>
      <SpinningArc />
      <span className="animate-[breatheText_2s_ease-in-out_infinite] text-xs font-medium tracking-wide text-accent-light">
        Thinking...
      </span>
    </IndicatorBox>
  );
}

export function ImageAnalyzingIndicator() {
  return (
    <IndicatorBox>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
        className="shrink-0 animate-[breatheIcon_2s_ease-in-out_infinite] text-accent-light">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
        <circle cx="8.5" cy="8.5" r="1.5"/>
        <polyline points="21 15 16 10 5 21"/>
      </svg>
      <span className="animate-[breatheText_2s_ease-in-out_infinite] text-xs font-medium tracking-wide text-accent-light">
        Analyzing Image...
      </span>
    </IndicatorBox>
  );
}

export const TypingIndicator = () => {
  return (
    <div className="flex items-center gap-1.5 px-1 py-2">
      {[0, 1, 2].map(i => (
        <div key={i} 
          className="h-2 w-2 animate-[typingBounce_1.2s_ease-in-out_infinite] rounded-full bg-accent-light"
          style={{ animationDelay: `${i * 0.2}s` }}
        />
      ))}
      <style>{sharedStyles}</style>
    </div>
  );
};

export default TypingIndicator;
