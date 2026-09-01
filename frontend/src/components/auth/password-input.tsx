"use client";

import { forwardRef, useState } from"react";
import { Eye, EyeOff } from"lucide-react";

import { cn } from"@/lib/utils";

export type PasswordInputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const PasswordInput = forwardRef<HTMLInputElement, PasswordInputProps>(
 ({ className, disabled, ...props }, ref) => {
 const [show, setShow] = useState(false);

 return (
 <div className="relative">
 <input
 {...props}
 ref={ref}
 type={show ?"text":"password"}
 disabled={disabled}
 className={cn(
"w-full rounded-md border border-salesos-border px-3 py-2 pr-10 text-sm outline-none placeholder:text-salesos-text-secondary/60 disabled:opacity-50",
 className,
 )}
 />
 <button
 type="button"
 onClick={() => setShow((s) => !s)}
 disabled={disabled}
 aria-label={show ?"Hide password":"Show password"}
 className="absolute inset-y-0 right-0 flex items-center pr-3 text-salesos-text-secondary/60 hover:text-salesos-text-secondary disabled:pointer-events-none"
 >
 {show ? (
 <EyeOff className="h-4 w-4"aria-hidden="true"/>
 ) : (
 <Eye className="h-4 w-4"aria-hidden="true"/>
 )}
 </button>
 </div>
 );
 },
);
PasswordInput.displayName ="PasswordInput";
