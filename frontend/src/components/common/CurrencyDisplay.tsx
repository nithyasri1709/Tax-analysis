import React from 'react';

interface CurrencyDisplayProps {
  amount?: number | null;
  className?: string;
  showSign?: boolean;
  prefix?: string;
}

export const formatINR = (value?: number | null): string => {
  if (value === undefined || value === null || isNaN(value)) {
    return '₹ 0';
  }
  const isNegative = value < 0;
  const absValue = Math.abs(Math.round(value));

  // Format using Indian numbering system
  const str = absValue.toString();
  let lastThree = str.substring(str.length - 3);
  const otherNumbers = str.substring(0, str.length - 3);
  if (otherNumbers !== '') {
    lastThree = ',' + lastThree;
  }
  const formatted = otherNumbers.replace(/\B(?=(\d{2})+(?!\d))/g, ',') + lastThree;

  return `${isNegative ? '-' : ''}₹ ${formatted}`;
};

export const CurrencyDisplay: React.FC<CurrencyDisplayProps> = ({
  amount = 0,
  className = '',
  showSign = false,
  prefix = '',
}) => {
  const sign = showSign && (amount ?? 0) > 0 ? '+' : '';
  return (
    <span className={`font-mono font-medium ${className}`}>
      {prefix}
      {sign}
      {formatINR(amount)}
    </span>
  );
};
