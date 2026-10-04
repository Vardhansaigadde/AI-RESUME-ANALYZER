import { useLayoutEffect, useRef, useState } from 'react';
import ResumeDocument from './ResumeDocument';

const PAGE_WIDTH = 793.7; // A4 at 96 dpi (595.3pt)
const PAGE_HEIGHT = 1122.5; // 841.9pt

/**
 * A resume page scaled to fit its container's width, like a print preview.
 * With `showPages`, dashed lines mark where each A4 page ends.
 */
export default function ScaledPage({ resume, templateId, accent, showPages = false, onPages }) {
  const box = useRef(null);
  const doc = useRef(null);
  const [scale, setScale] = useState(0.5);
  const [height, setHeight] = useState(PAGE_HEIGHT);

  useLayoutEffect(() => {
    const measure = () => {
      if (!box.current || !doc.current) return;
      setScale(box.current.clientWidth / PAGE_WIDTH);
      const h = Math.max(doc.current.offsetHeight, PAGE_HEIGHT);
      setHeight(h);
      onPages?.(Math.max(1, Math.ceil((h - 2) / PAGE_HEIGHT)));
    };
    measure();
    const observer = new ResizeObserver(measure);
    if (box.current) observer.observe(box.current);
    if (doc.current) observer.observe(doc.current);
    return () => observer.disconnect();
  }, [onPages]);

  const pages = Math.max(1, Math.ceil((height - 2) / PAGE_HEIGHT));
  return (
    <div ref={box} className="relative w-full overflow-hidden" style={{ height: height * scale }} aria-hidden={!showPages}>
      <div ref={doc} className="absolute top-0 left-0 origin-top-left" style={{ width: PAGE_WIDTH, transform: `scale(${scale})` }}>
        <ResumeDocument resume={resume} templateId={templateId} accent={accent} />
        {showPages &&
          Array.from({ length: pages - 1 }, (_, i) => (
            <div
              key={i}
              className="pointer-events-none absolute inset-x-0 border-t-2 border-dashed border-pen/60"
              style={{ top: PAGE_HEIGHT * (i + 1) }}
            >
              <span className="absolute right-2 -top-6 rounded bg-pen px-2 py-0.5 text-xs font-bold text-white">
                Page {i + 2}
              </span>
            </div>
          ))}
      </div>
    </div>
  );
}
