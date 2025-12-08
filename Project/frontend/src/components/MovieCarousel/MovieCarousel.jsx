import "./MovieCarousel.css";
import SmallMovie from "../SmallMovie/SmallMovie";
import { useRef, useState, useEffect } from "react";
import axios
    from "axios";
const MovieCarousel = ({ title }) => {
    
    const [moviesData, setMoviesData] = useState([]);

    const scrollRef = useRef(null);
    const lastScrollTime = useRef(0);
    const throttleDelay = 12;

    const handleWheel = (e) => {
        if (scrollRef.current) {
            const now = Date.now();
            if (now - lastScrollTime.current >= throttleDelay) {
                scrollRef.current.scrollLeft += (e.deltaY * 3);
                lastScrollTime.current = now;
            }

        }
    }


    useEffect(() => {axios.get('api/movies/trending/', {}).then((response) => {
        setMoviesData(response.data.results);
    })}, []);

    

    return (
        <div className="carousel-container" >
            <div>{title}</div>
            <div className="movies-wrapper" onWheel={handleWheel} ref={scrollRef}>
                {moviesData.map((movie) => (
                    <SmallMovie key={movie.id} movie={movie} />
                ))} 
            </div>
        </div>
    )
}

export default MovieCarousel;