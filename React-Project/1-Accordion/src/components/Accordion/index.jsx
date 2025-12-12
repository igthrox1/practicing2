import { useState } from "react";
import data from "./data.js";
import "./style.css";

function Accordian() {
  const [selected, setSelected] = useState(null);
  const [enableMultiSelection, setEnableMultiSelection] = useState(false);
  const [multiple, setMultiple] = useState([]);


  const handleSingleSelection = (getCurrentId) => {
    setSelected(getCurrentId === selected ? null : getCurrentId);
  };

  const handleMultiSelection = (getCurrentId) => {
    let cpyMultiple = [...multiple];
    let findIndexOfCurrentId = cpyMultiple.indexOf(getCurrentId);

    if(findIndexOfCurrentId === -1){
      cpyMultiple.push(getCurrentId)
    } else {
      cpyMultiple.splice(findIndexOfCurrentId , 1)
    }

    setMultiple(cpyMultiple)
  };



  return (
    <div className="wrapper">
      <button onClick={() => setEnableMultiSelection(!enableMultiSelection)}>
        Enable MultiSelection Tab
      </button>
      <div className="Accordion">
         {data && data.length > 0 ? (
          data.map((dataItems) => (
            <div className="item">
              <div
                className="title"
                onClick={
                  enableMultiSelection
                    ? () => handleMultiSelection(dataItems.id)
                    : () => handleSingleSelection(dataItems.id)
                }
              >
                <h3>{dataItems.title}</h3>
                <span>+</span>
              </div>
              {
                enableMultiSelection ? multiple.indexOf(dataItems.id) !== -1 && <div className="content">{dataItems.content}</div> : selected === dataItems.id ? (
                <div className="content">{dataItems.content}</div>
              ) : null
              }
              
            </div> 
          ))
        ) : (
          <h1>No data Found!</h1>
        )}
      </div>
    </div>
  );
}

export default Accordian;
