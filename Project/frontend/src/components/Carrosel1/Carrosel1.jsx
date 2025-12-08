import React, { useRef } from 'react';
import './Carrosel1.css';

const Carrosel1 = ({ slides = [] }) => {
  const sliderRef = useRef(null);

  const handleNext = () => {
    const slider = sliderRef.current;
    const items = slider.querySelectorAll('.item');
    slider.appendChild(items[0]);
  };

  const handlePrev = () => {
    const slider = sliderRef.current;
    const items = slider.querySelectorAll('.item');
    slider.prepend(items[items.length - 1]);
  };

  const handleCardClick = (e) => {
    const slider = sliderRef.current;
    const items = Array.from(slider.querySelectorAll('.item'));
    const clickedItem = e.currentTarget;
    const index = items.indexOf(clickedItem);

    if (index > 1) {
      const moves = index - 1; 
      for (let i = 0; i < moves; i++) {
        slider.appendChild(slider.querySelectorAll('.item')[0]);
      }
    }
  };

  if (!slides.length) return null;

  return (
    <main className="container">
      <ul className="slider" ref={sliderRef}>
        {slides.map((item, index) => (
          <li
            key={index}
            className="item"
            style={{ backgroundImage: `url(${item.img})` }}
            onClick={handleCardClick}
          >
            <div className="content">
              <h2 className="title">{item.title}</h2>
              <p className="description">{item.desc}</p>
              <button>Read More</button>
            </div>
          </li>
        ))}
      </ul>

      <nav className="nav">
        <button className="btn prev" onClick={handlePrev}>
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <button className="btn next" onClick={handleNext}>
           <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
        </button>
      </nav>
    </main>
  );
};

export default Carrosel1;