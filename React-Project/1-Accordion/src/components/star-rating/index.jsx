import { FaStar } from "react-icons/fa"
import {useState} from "react"
import './style.css'

function StarRating({noOfStars = 5}) {
    const [rating , setRating ] = useState(0)
    const [hover , setHover] = useState(0)

    const handleClick=(getCurrentIndex) => {
        setRating(getCurrentIndex)
    }

     const hnadleMouseEnter=(getCurrentIndex) => {
        setHover(getCurrentIndex)
    }

     const handleMouseLeave=() => {
        setHover(rating)
    }
    
    return <div>
        {
            [...Array(noOfStars)].map((_,index) => {
                index +=1
                return <FaStar
                key={index}
                className={index <= (hover || rating)? "Active" : "Inactive" }
                onClick ={() => {handleClick(index)}}
                onMouseMove ={() => {hnadleMouseEnter(index)}}
                onMouseLeave={() => {handleMouseLeave()}}
                size={40} />
            }) 
        },

    </div>
}


export default StarRating;