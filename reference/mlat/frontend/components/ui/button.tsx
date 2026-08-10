import { cva, type VariantProps } from 'class-variance-authority';
import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export const buttonVariants = cva(
  'inline-flex h-9 shrink-0 items-center justify-center gap-2 rounded-md px-3 text-[13px] font-semibold transition-[background-color,color,transform,border-color] duration-standard ease-operational focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-blue focus-visible:ring-offset-2 focus-visible:ring-offset-graphite-deep disabled:pointer-events-none disabled:opacity-45 active:scale-[0.98]',
  {
    variants: {
      variant: {
        primary: 'bg-signal-blue text-graphite-deep hover:bg-[#78adff]',
        secondary: 'border border-line bg-graphite-raised text-ink hover:border-[#3c4654] hover:bg-graphite-hover',
        ghost: 'text-ink-secondary hover:bg-graphite-hover hover:text-ink',
        danger: 'bg-failure/15 text-[#ff9ba0] hover:bg-failure/25',
      },
      size: {
        default: 'h-9 px-3',
        sm: 'h-8 px-2.5 text-xs',
        icon: 'size-9 p-0',
        'icon-sm': 'size-8 p-0',
      },
    },
    defaultVariants: { variant: 'secondary', size: 'default' },
  },
);

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(({ className, variant, size, ...props }, ref) => (
  <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
));
Button.displayName = 'Button';
