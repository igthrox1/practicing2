import { useEffect } from "react";
import { useState } from "react";
import { FaArrowRight } from "react-icons/fa";
import { FaArrowLeft } from "react-icons/fa";
import "./style.css";

function ImageSlider({ url, limit }) {
  const [images, setImages] = useState([]);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [errorMsg, setErrorMsg] = useState("");
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

  useEffect(() => {
    if (url !== "") fetchImages(url);
  }, [url]);

  if (loadingState) {
    return <div> loading</div>;
  }

  if (errorMsg !== "") {
    return <div>Error occured {errorMsg} </div>;
  }

  function handlePrevious() {
    setCurrentSlide(currentSlide === 0 ? images.length - 1 : currentSlide - 1);
  }

  function handleNext() {
    setCurrentSlide(currentSlide === images.length - 1 ? 0 : currentSlide + 1);
  }

  return (
    <div className="Container">
      <FaArrowLeft onClick={handlePrevious} className="arrow arrow-left" />
      {images && images.length
        ? images.map((imageItem, index) => (
            <img
              key={imageItem.id}
              alt={imageItem.download_url}
              src={imageItem.download_url}
              className={
                currentSlide === index
                  ? "current-image"
                  : " current-image hide-current-image"
              }
            />
          ))
        : null}
      <FaArrowRight onClick={handleNext} className="arrow arrow-Right" />
      <span className="circle-indicators">
        {images && images.length
          ? images.map((_, index) => (
              <button
                key={index}
                className={
                  currentSlide === index
                    ? "current-indicator"
                    : " current-indicator inactive-indicator"
                }
                onClick={()=> {setCurrentSlide(index)}}
              />
            ))
          : null}
      </span>
    </div>
  );
}

export default ImageSlider;
