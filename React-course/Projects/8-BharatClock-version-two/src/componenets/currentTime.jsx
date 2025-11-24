import { useEffect, useState } from "react";

let CurrentTime = () => {
  
  const [Time , setTime ] = useState(new Date());

  useEffect(() => {
    const intervalId = setInterval(() => {
      setTime(new Date())
    },1000);

    return () => {
      clearInterval(intervalId);
    }
  },[])
  
  return (
    <p className="Lead">
      This is the current time:{Time.toLocaleDateString()} -{" "}
      {Time.toLocaleTimeString()}
    </p>
  );
};

export default CurrentTime;
