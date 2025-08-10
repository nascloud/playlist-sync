import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

const iconButtonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none',
  {
    variants: {
      variant: {
        default: 'bg-transparent hover:bg-gray-100',
        danger: 'bg-transparent text-red-500 hover:bg-red-50',
      },
      size: {
        default: 'h-10 w-10',
        sm: 'h-8 w-8',
        lg: 'h-12 w-12',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof iconButtonVariants> {
  children: React.ReactNode;
  tooltip?: string;
}

const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ className, variant, size, children, tooltip, ...props }, ref) => {
    return (
      <div className="relative group">
        <button
          className={iconButtonVariants({ variant, size, className })}
          ref={ref}
          {...props}
        >
          {children}
          <span className="sr-only">{tooltip}</span>
        </button>
        {tooltip && (
          <div className="absolute bottom-full mb-2 hidden group-hover:block w-max bg-gray-800 text-white text-xs rounded py-1 px-2">
            {tooltip}
          </div>
        )}
      </div>
    );
  }
);

IconButton.displayName = 'IconButton';

export default IconButton;
