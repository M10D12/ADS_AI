import React, { useState } from 'react';
import './StarRating.css';

export default function StarRating({ 
  value, 
  onChange, 
  readOnly = false, 
  disabled = false, 
  name = "rating" 
}) {
  const [hoverValue, setHoverValue] = useState(null);

  const displayValue = hoverValue !== null ? hoverValue : value;

  const handleClick = (newValue) => {
    if (!readOnly && !disabled && onChange) {
      onChange(null, newValue);
    }
  };

  const handleMouseEnter = (newValue) => {
    if (!readOnly && !disabled) {
      setHoverValue(newValue);
    }
  };

  const handleMouseLeave = () => {
    setHoverValue(null);
  };

  const starsArray = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

  return (
    <div 
      className={`rating-container ${readOnly ? 'read-only' : ''} ${disabled ? 'disabled' : ''}`}
      onMouseLeave={handleMouseLeave}
    >
      {starsArray.map((starIndex) => {
        let visualClass = 'empty';
        
        if (displayValue >= starIndex) {
          visualClass = 'full';
        } else if (displayValue >= starIndex - 0.5) {
          visualClass = 'half';
        }

        return (
          <div key={starIndex} className="star-wrapper">
            <span className={`star-visual ${visualClass}`}>★</span>

            <span 
              className="hitbox-left" 
              onClick={() => handleClick(starIndex - 0.5)}
              onMouseEnter={() => handleMouseEnter(starIndex - 0.5)}
            />
            <span 
              className="hitbox-right" 
              onClick={() => handleClick(starIndex)}
              onMouseEnter={() => handleMouseEnter(starIndex)}
            />
          </div>
        );
      })}
    </div>
  );
}