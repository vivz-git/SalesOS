import { Slot } from"@radix-ui/react-slot";
import { cva, type VariantProps } from"class-variance-authority";
import * as React from"react";

import { cn } from"@/lib/utils";

const buttonVariants = cva(
"inline-flex items-center justify-center gap-2 rounded-lg text-sm font-medium transition-colors duration-150 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 cursor-pointer",
 {
 variants: {
 variant: {
 // Primary — ONE per screen, dominant action
 primary:
"bg-salesos-brand text-white hover:bg-salesos-brand-hover shadow-sm",
 // Alias so existing code using variant="default"gets the primary style
 default:
"bg-salesos-brand text-white hover:bg-salesos-brand-hover shadow-sm",
 // Secondary — supporting actions
 secondary:
"border border-salesos-border bg-salesos-surface text-salesos-text-secondary hover:bg-salesos-surface-muted hover:text-salesos-text",
 // Alias for existing outline usage
 outline:
"border border-salesos-border bg-salesos-surface text-salesos-text-secondary hover:bg-salesos-surface-muted hover:text-salesos-text",
 // Destructive — for delete / reject actions
 destructive:
"border border-salesos-danger/20 bg-salesos-danger/10 text-salesos-danger hover:bg-salesos-danger/20",
 // Ghost — for icon-only or low-hierarchy actions
 ghost:
"text-salesos-text-secondary hover:bg-salesos-surface-muted hover:text-salesos-text",
 },
 size: {
 default:"h-9 px-4 py-2",
 sm:"h-8 px-3 text-xs",
 lg:"h-10 px-6",
 icon:"h-9 w-9 p-0",
 },
 },
 defaultVariants: { variant:"default", size:"default"},
 },
);

export interface ButtonProps
 extends React.ButtonHTMLAttributes<HTMLButtonElement>,
 VariantProps<typeof buttonVariants> {
 asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
 ({ asChild = false, className, size, variant, ...props }, ref) => {
 const Component = asChild ? Slot :"button";
 return (
 <Component
 className={cn(buttonVariants({ size, variant, className }))}
 ref={ref}
 {...props}
 />
 );
 },
);
Button.displayName ="Button";

export { Button, buttonVariants };
