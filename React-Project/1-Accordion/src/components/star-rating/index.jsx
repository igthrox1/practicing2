import { FaStar } from "react-icons/fa"

function StarRating(noOfStars = 5) {
    return <div>
        {
            [...Array(noOfStars)].map((_,index) => {
                return <FaStar/>
            })
        }
    </div>
}

export default StarRating;