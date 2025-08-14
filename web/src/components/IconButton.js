import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import React from 'react';
import { cva } from 'class-variance-authority';
const iconButtonVariants = cva('inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none', {
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
});
const IconButton = React.forwardRef(({ className, variant, size, children, tooltip, ...props }, ref) => {
    return (_jsxs("div", { className: "relative group", children: [_jsxs("button", { className: iconButtonVariants({ variant, size, className }), ref: ref, ...props, children: [children, _jsx("span", { className: "sr-only", children: tooltip })] }), tooltip && (_jsx("div", { className: "absolute bottom-full mb-2 hidden group-hover:block w-max bg-gray-800 text-white text-xs rounded py-1 px-2", children: tooltip }))] }));
});
IconButton.displayName = 'IconButton';
export default IconButton;
