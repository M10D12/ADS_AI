import "./SmallMovie.css";

const SmallMovie = ({ movie }) => {
    // por pra ir pra pagina do filme ao clciar
    console.log(movie);
    const img = "https://image.tmdb.org/t/p/w500" + movie.backdrop_path ;
    return (
        <div className="small-movie-container" >
            <img src={img} alt={movie.title} onClick={() => {}}/>
        </div>
    )
}

export default SmallMovie;