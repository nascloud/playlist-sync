import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useRef } from 'react';
const Modal = ({ isOpen, onClose, title, children, size = 'md' }) => {
    const modalRef = useRef(null);
    useEffect(() => {
        const handleEsc = (event) => {
            if (event.key === 'Escape') {
                onClose();
            }
        };
        if (isOpen) {
            document.addEventListener('keydown', handleEsc);
            modalRef.current?.focus();
        }
        return () => {
            document.removeEventListener('keydown', handleEsc);
        };
    }, [isOpen, onClose]);
    if (!isOpen)
        return null;
    const sizeClasses = {
        md: 'max-w-md',
        lg: 'max-w-lg',
        xl: 'max-w-xl',
        '2xl': 'max-w-2xl',
        '4xl': 'max-w-4xl',
    };
    const modalSize = sizeClasses[size];
    return (_jsx("div", { className: "fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center", role: "dialog", "aria-modal": "true", "aria-labelledby": "modal-title", onClick: onClose, children: _jsxs("div", { ref: modalRef, className: `bg-white rounded-lg shadow-xl w-full ${modalSize}`, onClick: (e) => e.stopPropagation(), tabIndex: -1, children: [_jsxs("div", { className: "p-4 border-b flex justify-between items-center", children: [_jsx("h3", { id: "modal-title", className: "text-lg font-semibold", children: title }), _jsx("button", { onClick: onClose, className: "text-gray-500 hover:text-gray-800", "aria-label": "Close modal", children: "\u00D7" })] }), _jsx("div", { className: "p-4", children: children })] }) }));
};
export default Modal;
