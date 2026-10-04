import { createPortal } from 'react-dom';
import { DENSITY, templateById } from '../../lib/templates';
import ResumeDocument from './ResumeDocument';

/**
 * A print-only copy of the resume, outside the app root, so "Save as PDF" produces
 * just the resume with real, selectable text. The page margin comes from the template.
 */
export default function PrintResume({ resume, templateId, accent }) {
  const margin = DENSITY[templateById(templateId).density].margin;
  return createPortal(
    <div id="print-root">
      <style>{`@page { size: A4; margin: ${margin}pt; }`}</style>
      <ResumeDocument resume={resume} templateId={templateId} accent={accent} print />
    </div>,
    document.body,
  );
}
