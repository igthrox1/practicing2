import { useEffect, useState } from "react";
import "./styles.css";

function loadMoreData() {
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState([]);
  const [count, setCount] = useState(0);
  const [disableButton , setDisableButton] = useState(false)
  async function fetchProducts() {
    try {
      setLoading(true);
      const response = await fetch(
        `https://dummyjson.com/products?limit=20&skip=${
          count == 0 ? 0 : count * 20
        }`
      );
      const result = await response.json();

      if (result && result.products && result.products.length) {
        setProducts((prevdata)=> [...prevdata , ...result.products])
        setLoading(false);
      }

      console.log(result);
    } catch (e) {
      console.log(e);
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchProducts();
  }, [count]);

  useEffect(()=> {
    if(products && products.length === 100){
      setDisableButton(true)
    }
  },[products])

  if (loading) {
    return <div>The data is loading </div>;
  }

  return (
    <div className="container">
      <div className="product-container">
        {products && products.length
          ? products.map((item) => (
              <div className="product" key={item.id}>
                <img src={item.thumbnail} alt={item.title} />
                <p>{item.title}</p>
              </div>
            ))
          : null}
      </div>
      <div>
        <button
        disabled ={disableButton}
          className="button-container"
          onClick={() => {
            setCount(count + 1);
          }}
        >
          load More Products
        </button>
        {
          disableButton ? <p>
            You have Reached the end of Products
          </p> : null
        }
      </div>
    </div>
  );
}

export default loadMoreData;
