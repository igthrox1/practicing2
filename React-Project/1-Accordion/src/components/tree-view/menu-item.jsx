import MenuList from "./menu-list";
import { useState } from "react";
import { FaPlus } from "react-icons/fa";
import { RiSubtractFill } from "react-icons/ri";



function MenuItem({item}){
    const [displayCurrentChildren , setDisplayCurrentChildren] = useState({})

    function handleToggleChildren(getCurrentLabel) {
        setDisplayCurrentChildren({
            ...displayCurrentChildren ,
            [getCurrentLabel]:!displayCurrentChildren[getCurrentLabel]
        })
    }
    
    console.log(displayCurrentChildren)
    return <li >
        <div className="menu-item" style = {{ display:"flex" , gap:"20px"}}>
             {item.label}
             
             {
                item && item.children && item.children.length ? <span onClick={() => {handleToggleChildren(item.label)}}>
                    {
                        displayCurrentChildren[item.label] ? <RiSubtractFill color="white" size="20px" />: <FaPlus color="white" size="20px"/>
                    }
                </span> : null
             }
        </div>

        {
        item && item.children && item.children.length >0 && displayCurrentChildren[item.label] ?(
        <MenuList list = {item.children} />)
        : null
    }
    </li>

    
}

export default MenuItem;