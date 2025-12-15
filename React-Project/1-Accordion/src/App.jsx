import Accordian from "./components/Accordion"
import ImageSlider from "./components/img-slider"
import RandomColor from "./components/random-color"
import StarRating from "./components/star-rating"
import LoadMoreData from "./components/load-more-data"
import TreeView from "./components/tree-view"
import menus from "./components/tree-view/data"

function App() {
  

  return (
    <>
      <Accordian/>
      <RandomColor />
      <StarRating/>
      <ImageSlider url = {'https://picsum.photos/v2/list'} limit = {10}/>
      <LoadMoreData/>
      <TreeView menus ={menus} />
    </>
  )
}

export default App
