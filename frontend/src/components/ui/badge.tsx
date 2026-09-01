import { cva, type VariantProps } from"class-variance-authority";
import * as React from"react";
import { cn } from"@/lib/utils";

const badgeVariants = cva(
"inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium",
 {
 variants: {
 variant: {
 default:"bg-slate-100 text-slate-700",
 success:"bg-emerald-50 text-emerald-800",
 warning:"bg-amber-50 text-amber-800",
 error:"bg-red-50 text-red-700",
 info:"bg-blue-50 text-blue-800",
 accent:"bg-indigo-50 text-indigo-800",
 },
 },
 defaultVariants: { variant:"default"},
 },
);

export interface BadgeProps
 extends React.HTMLAttributes<HTMLSpanElement>,
 VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
 return (
 <span className={cn(badgeVariants({ variant }), className)} {...props} />
 );
}

export { Badge, badgeVariants };
