import { motion } from 'framer-motion';
import AddJobBar from './overview/AddJobBar';
import GithubCheck from './overview/GithubCheck';
import { JobSummary, ScoreBreakdown } from './overview/JobMatch';
import { SectionLabel } from './overview/Panel';
import { SkillsFound, StrengthReport, TargetRole } from './overview/ResumeProfile';

/** Overview: the job match (when there is a job) and the resume's own profile. */
export default function OverviewTab({ result, draft, onEdit, onRoleChange, roleLoading, addJob, github }) {
  const resumeOnly = result.mode === 'resume_only';
  return (
    <motion.div
      initial="hidden"
      animate="show"
      variants={{ show: { transition: { staggerChildren: 0.06 } } }}
      className="grid gap-5 lg:grid-cols-5"
    >
      {resumeOnly ? (
        <AddJobBar {...addJob} />
      ) : (
        <>
          <SectionLabel>Job match</SectionLabel>
          <JobSummary insights={result.job_insights} matched={result.matched_skills} missing={result.missing_skills} />
          <ScoreBreakdown breakdown={result.score_breakdown} warnings={result.score_warnings} />
        </>
      )}

      <SectionLabel>Your resume</SectionLabel>
      <StrengthReport resume={draft} studentMode={result.student_mode} onEdit={onEdit} />
      <div className="lg:col-span-3">
        <TargetRole
          gap={result.role_gap}
          roles={result.suggested_roles}
          confidence={result.confidence}
          onRoleChange={onRoleChange}
          loading={roleLoading}
        />
      </div>
      <div className="lg:col-span-2">
        <SkillsFound groups={result.skills_inventory || []} />
      </div>
      <GithubCheck resume={draft} {...github} />
    </motion.div>
  );
}
