import Accordian from "./components/Accordion"
import ImageSlider from "./components/img-slider"
import RandomColor from "./components/random-color"
import StarRating from "./components/star-rating"

function App() {
  

  return (
    <>
      <Accordian/>
      <RandomColor />
      <StarRating/>
      <ImageSlider url = {'https://picsum.photos/v2/list'} limit = {10}/>
    </>
  )
}

export default App
