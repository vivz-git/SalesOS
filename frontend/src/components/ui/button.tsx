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
"bg-accent text-accent-foreground hover:bg-accent-hover shadow-sm",
 // Alias so existing code using variant="default"gets the primary style
 default:
"bg-accent text-accent-foreground hover:bg-accent-hover shadow-sm",
 // Secondary — supporting actions
 secondary:
"border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 hover:text-slate-900",
 // Alias for existing outline usage
 outline:
"border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 hover:text-slate-900",
 // Destructive — for delete / reject actions
 destructive:
"border border-red-200 bg-red-50 text-red-700 hover:bg-red-100",
 // Ghost — for icon-only or low-hierarchy actions
 ghost:
"text-slate-600 hover:bg-slate-100 hover:text-slate-900",
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
