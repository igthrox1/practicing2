import FetchItems from "../components/fetchItems";
import Footer from "../components/footer";
import Header from "../components/header";
import { Outlet } from "react-router-dom";
import { useSelector } from "react-redux";
import Loader from "../components/loadingSpinner";

function App() {
  
  const fetchStatus = useSelector(Store => Store.fetchStatus)

  return (
    <>
      <Header />
      <FetchItems />
      {fetchStatus.currentlyFetching ? <Loader /> : <Outlet />}
      <Footer />
    </>
  );
}

export default App;
