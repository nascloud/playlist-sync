import React, { memo } from 'react';

type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string;
};

const Input: React.FC<InputProps> = ({
  label,
  error,
  className = '',
  id,
  name,
  ...props
}) => {
  const inputId = id || name;
  const baseClasses = 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2';
  const errorClasses = 'border-red-500 focus:ring-red-500';
  const defaultClasses = 'border-gray-300 focus:ring-blue-500';

  return (
    <div className="mb-4">
      <label htmlFor={inputId} className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <input
        id={inputId}
        name={name}
        className={`${baseClasses} ${error ? errorClasses : defaultClasses} ${className}`}
        {...props}
      />
      {error && <p className="mt-1 text-sm text-red-500">{error}</p>}
    </div>
  );
};

export default memo(Input);
