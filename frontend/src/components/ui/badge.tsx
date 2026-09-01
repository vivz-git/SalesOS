import { cva, type VariantProps } from"class-variance-authority";
import * as React from"react";
import { cn } from"@/lib/utils";

const badgeVariants = cva(
"inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium",
 {
 variants: {
 variant: {
 default:"bg-salesos-surface-muted text-salesos-text-secondary",
 success:"bg-salesos-success/10 text-salesos-success",
 warning:"bg-salesos-warning/10 text-salesos-warning",
 error:"bg-salesos-danger/10 text-salesos-danger",
 info:"bg-salesos-info/10 text-salesos-info",
 accent:"bg-salesos-brand-subtle text-salesos-brand",
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
