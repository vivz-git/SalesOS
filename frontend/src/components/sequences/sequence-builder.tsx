"use client";

import { useState } from"react";
import {
 saveCampaignSequence,
 type SequenceDefinition,
 type SequenceStepPayload,
} from"@/lib/api/sequences";
import { Plus, Trash2, Save, Layers, Clock, Mail } from"lucide-react";

interface SequenceBuilderProps {
 workspaceId: string;
 campaignId: string;
 initialSequence: SequenceDefinition;
 onSaved?: (updated: SequenceDefinition) => void;
}

export function SequenceBuilder({
 workspaceId,
 campaignId,
 initialSequence,
 onSaved,
}: SequenceBuilderProps) {
 const [name, setName] = useState<string>(initialSequence.name ||"Outreach Sequence");
 const [steps, setSteps] = useState<SequenceStepPayload[]>(
 initialSequence.steps && initialSequence.steps.length > 0
 ? initialSequence.steps.map((st) => ({
 step_number: st.step_number,
 delay_days: st.delay_days,
 channel: st.channel,
 step_type: st.step_type,
 template_subject: st.template_subject ||"",
 template_body: st.template_body ||"",
 }))
 : [
 {
 step_number: 1,
 delay_days: 0,
 channel:"email",
 step_type:"first_touch",
 template_subject:"Introductory Outreach",
 template_body:"Hi {{first_name}}, reaching out regarding...",
 },
 {
 step_number: 2,
 delay_days: 3,
 channel:"email",
 step_type:"follow_up",
 template_subject:"Quick Follow-Up",
 template_body:"Hi {{first_name}}, following up on my previous note...",
 },
 ]
 );
 const [saving, setSaving] = useState<boolean>(false);
 const [msg, setMsg] = useState<string | null>(null);

 function handleAddStep() {
 const newStepNum = steps.length + 1;
 setSteps([
 ...steps,
 {
 step_number: newStepNum,
 delay_days: 3,
 channel:"email",
 step_type:"follow_up",
 template_subject: `Follow-up Touchpoint ${newStepNum}`,
 template_body:"Hi {{first_name}}, following up...",
 },
 ]);
 }

 function handleRemoveStep(idx: number) {
 if (steps.length <= 1) return;
 const updated = steps.filter((_, i) => i !== idx).map((s, i) => ({ ...s, step_number: i + 1 }));
 setSteps(updated);
 }

 function handleStepChange(idx: number, field: keyof SequenceStepPayload, val: unknown) {
 const updated = [...steps];
 updated[idx] = { ...updated[idx], [field]: val };
 setSteps(updated);
 }

 async function handleSave() {
 setSaving(true);
 setMsg(null);
 try {
 const updatedSeq = await saveCampaignSequence(workspaceId, campaignId, name, steps);
 setMsg(`Saved sequence v${updatedSeq.version_number}`);
 if (onSaved) onSaved(updatedSeq);
 setTimeout(() => setMsg(null), 4000);
 } catch (err: unknown) {
 setMsg(err instanceof Error ? err.message :"Failed to save sequence");
 } finally {
 setSaving(false);
 }
 }

 return (
 <div className="rounded-xl border border-salesos-border bg-salesos-surface p-6 shadow-sm space-y-6">
 <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-salesos-border pb-4">
 <div>
 <h2 className="text-base font-bold text-salesos-text flex items-center gap-2">
 <Layers className="h-5 w-5 text-salesos-brand"/>
 <span>Campaign Sequence Builder</span>
 </h2>
 <p className="text-xs text-salesos-text-secondary">
 Define multi-step outreach touchpoints, delay rules, and email templates.
 </p>
 </div>

 <button
 type="button"
 onClick={handleSave}
 disabled={saving}
 className="inline-flex items-center gap-1.5 rounded-lg bg-salesos-brand px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-salesos-brand-hover transition-colors shrink-0 shadow-sm focus:outline-none"
 >
 <Save className="h-3.5 w-3.5"/>
 <span>{saving ?"Saving...":"Save Sequence Definition"}</span>
 </button>
 </div>

 {msg && (
 <div className="rounded-lg border border-salesos-brand/20 bg-salesos-brand-subtle p-3 text-xs font-semibold text-salesos-brand">
 {msg}
 </div>
 )}

 <div>
 <label className="text-xs font-semibold text-salesos-text-secondary">Sequence Name</label>
 <input
 type="text"
 value={name}
 onChange={(e) => setName(e.target.value)}
 className="mt-1 w-full max-w-md rounded-lg border border-salesos-border p-2 text-xs text-salesos-text focus:border-salesos-focus focus:outline-none"
 />
 </div>

 {/* Steps List */}
 <div className="space-y-4">
 <h3 className="text-xs font-semibold uppercase tracking-wider text-salesos-text-secondary/60">
 Sequence Touchpoint Steps ({steps.length})
 </h3>

 {steps.map((st, idx) => (
 <div key={idx} className="rounded-xl border border-salesos-border bg-salesos-surface-muted p-4 space-y-3">
 <div className="flex items-center justify-between">
 <div className="flex items-center gap-2">
 <span className="flex h-6 w-6 items-center justify-center rounded-full bg-salesos-brand-subtle text-xs font-bold text-salesos-brand">
 {st.step_number}
 </span>
 <span className="text-xs font-bold text-salesos-text capitalize">
 {(st.step_type ||"follow_up").replace(/_/g,"")} ({st.channel ||"email"})
 </span>
 </div>

 {steps.length > 1 && (
 <button
 type="button"
 onClick={() => handleRemoveStep(idx)}
 className="p-1 text-salesos-text-secondary/60 hover:text-salesos-danger transition-colors focus:outline-none rounded-sm"
 title="Remove step"
 >
 <Trash2 className="h-4 w-4"/>
 </button>
 )}
 </div>

 <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 text-xs">
 <div>
 <label className="font-semibold text-salesos-text-secondary flex items-center gap-1">
 <Clock className="h-3 w-3 text-salesos-text-secondary/60"/>
 Delay Days After Previous Step
 </label>
 <input
 type="number"
 min={0}
 max={90}
 value={st.delay_days}
 onChange={(e) => handleStepChange(idx,"delay_days", parseInt(e.target.value) || 0)}
 className="mt-1 w-full rounded-lg border border-salesos-border bg-salesos-surface p-2 text-xs text-salesos-text focus:border-salesos-focus focus:outline-none"
 />
 </div>

 <div className="sm:col-span-2">
 <label className="font-semibold text-salesos-text-secondary flex items-center gap-1">
 <Mail className="h-3 w-3 text-salesos-text-secondary/60"/>
 Template Subject Line
 </label>
 <input
 type="text"
 value={st.template_subject ||""}
 onChange={(e) => handleStepChange(idx,"template_subject", e.target.value)}
 className="mt-1 w-full rounded-lg border border-salesos-border bg-salesos-surface p-2 text-xs text-salesos-text focus:border-salesos-focus focus:outline-none"
 />
 </div>
 </div>

 <div className="text-xs">
 <label className="font-semibold text-salesos-text-secondary">Template Body Content</label>
 <textarea
 rows={3}
 value={st.template_body ||""}
 onChange={(e) => handleStepChange(idx,"template_body", e.target.value)}
 className="mt-1 w-full rounded-lg border border-salesos-border bg-salesos-surface p-2 text-xs font-normal text-salesos-text focus:border-salesos-focus focus:outline-none"
 />
 </div>
 </div>
 ))}
 </div>

 <button
 type="button"
 onClick={handleAddStep}
 className="inline-flex items-center gap-1.5 rounded-lg border border-dashed border-salesos-border px-3.5 py-2 text-xs font-semibold text-salesos-text-secondary hover:bg-salesos-surface-muted transition-colors focus:outline-none"
 >
 <Plus className="h-4 w-4"/>
 <span>Add Follow-Up Step</span>
 </button>
 </div>
 );
}
