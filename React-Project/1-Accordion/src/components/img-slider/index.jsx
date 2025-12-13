import { useEffect } from "react";
import { useState } from "react";
import { FaArrowRight } from "react-icons/fa";
import { FaArrowLeft } from "react-icons/fa";
import "./style.css"

function ImageSlider({ url, limit }) {
  const [images, setImages] = useState([]);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [errorMsg, setErrorMsg] = useState('');
  const [loadingState, setLoadingState] = useState(false);

  async function fetchImages(getUrl) {
    try {
      setLoadingState(true);
      const response = await fetch(`${getUrl}?limit=${limit}`);
      const data = await response.json();

      if (data) {
        setImages(data);
        setLoadingState(false);
      }
    } catch (e) {
      setErrorMsg(e.message);
    }
  }
  console.log(images);

  useEffect(() => {
    if (url !== "") fetchImages(url);
  }, [url]);

  if (loadingState) {
    return <div> loading</div>;
  }

  if (errorMsg !== "") {
    return <div>Error occured {errorMsg} </div>;
  }

  return (
    <div className="Container">
      <FaArrowRight className="arrow arrow-left" />
      {images && images.length
        ? images.map((imageItem) => (
            <img
              key={imageItem.id}
              alt={imageItem.download_url}
              src={imageItem.download_url}
              className="current-image"
            />
          ))
        : null}
      <FaArrowLeft className="arrow arrow-Right" />
      <span className="circle-indicators">
          {
            images && images.length ? 
            images.map((_,index)=><button 
            key={index}
            className="current-indicator" />)
            :null
          }
      </span>
    </div>
  );
}

export default ImageSlider;
