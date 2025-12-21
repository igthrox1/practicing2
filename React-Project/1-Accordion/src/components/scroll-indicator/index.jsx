import { useEffect } from "react";
import { useState } from "react";

function ScrollIndicator({url}) {
    
    const [data , setData] = useState([]);

    const [loading , setLoading] = useState(false);

    const [errorMsg , setErrorMsg] = useState("");

    async function fetchData({url}) {
        try{
            setLoading(true);

            const response = await fetch (url);
            const data = await response.json();

            console.log(data);

        }catch(e){
            console.log(e);
            setErrorMsg(e.message);
        }
    }

    useEffect(() => {
        fetchData(url);
    },[])
    
    return <div>

    </div>
}

export default ScrollIndicator;