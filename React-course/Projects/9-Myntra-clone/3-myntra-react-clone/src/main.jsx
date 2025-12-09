import { createRoot } from 'react-dom/client'
import './index.css'
import App from './routes/App.jsx'
import { createBrowserRouter , RouterProvider } from "react-router-dom";
import Bag from './routes/bag.jsx';
import Home from './routes/home.jsx';
import { Provider } from 'react-redux';
import MyntraStore from './store/index.js';
import "bootstrap/dist/css/bootstrap.min.css";

const Router = createBrowserRouter([
  {
    path : "/",
    element : <App />,
    children:[
      {path : "/", element : <Home /> },
      {path : "/bag", element : <Bag />}
    ]
  },
]);


createRoot(document.getElementById('root')).render(
    <Provider store = {MyntraStore} > 
      <RouterProvider router = { Router } />
    </Provider>
)
