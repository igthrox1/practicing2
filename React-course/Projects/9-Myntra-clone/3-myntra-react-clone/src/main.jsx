import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { createBrowserRouter , RouterProvider } from "react-router-dom";

const Router = createBrowserRouter([
  {
    path : "/",
    element : <App />,
    hydrateFallbackElement: <LoadingSpinner />,
    children:[
      {path : "/", element : <PostList /> , loader : PostLoader},
      {path : "/create-Post", element : <CreatePost /> , action: CreatePostAction },
    ]
  },
]);


createRoot(document.getElementById('root')).render(
  <StrictMode>
    <RouterProvider router = { Router } />
  </StrictMode>,
)
