import { cn } from"@/lib/utils";

interface PasswordStrengthProps {
 password: string;
}

interface StrengthResult {
 score: number;
 label: string;
 color: string;
}

/** Returns a 0-5 score based on password complexity criteria. */
export function getPasswordStrength(password: string): StrengthResult {
 if (!password) return { score: 0, label:"", color:""};

 let score = 0;
 if (password.length >= 8) score++;
 if (/[A-Z]/.test(password)) score++;
 if (/[a-z]/.test(password)) score++;
 if (/[0-9]/.test(password)) score++;
 if (/[^A-Za-z0-9]/.test(password)) score++;

 const levels: Array<{ label: string; color: string }> = [
 { label:"", color:""},
 { label:"Weak", color:"bg-red-500"},
 { label:"Fair", color:"bg-orange-400"},
 { label:"Good", color:"bg-yellow-400"},
 { label:"Strong", color:"bg-green-500"},
 { label:"Strong", color:"bg-green-500"},
 ];

 return { score, ...levels[score] };
}

const SEGMENTS = 4;

export function PasswordStrength({ password }: PasswordStrengthProps) {
 if (!password) return null;

 const { score, label, color } = getPasswordStrength(password);
 const filled = Math.round((score / 5) * SEGMENTS);

 return (
 <div className="mt-2 space-y-1.5"aria-live="polite"aria-label={`Password strength: ${label}`}>
 <div className="flex gap-1"role="presentation">
 {Array.from({ length: SEGMENTS }, (_, i) => (
 <div
 key={i}
 className={cn(
"h-1 flex-1 rounded-full transition-colors duration-200",
 i < filled ? color :"bg-slate-200",
 )}
 />
 ))}
 </div>
 {label && (
 <p className="text-xs text-slate-500">
 Password strength:{""}
 <span className="font-medium text-slate-700">{label}</span>
 </p>
 )}
 </div>
 );
}
