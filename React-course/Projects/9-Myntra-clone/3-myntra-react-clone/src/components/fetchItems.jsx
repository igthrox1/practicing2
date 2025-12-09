import { useSelector , useDispatch } from "react-redux";
import { useEffect  } from "react";
import { itemsAction } from "../store/itemSlice";
import { fetchStatusAction } from "../store/fetchStatusSlice";

function FetchItems() {
    const fetchStatus = useSelector(Store => Store.fetchStatus)
    const dispatch = useDispatch();

    useEffect(() => {
        
        if (fetchStatus.fetchDone) return
        const controller = new AbortController();
        const signal = controller.signal;
        dispatch(fetchStatusAction.markFetchingStarted())
        fetch("http://127.0.0.1:8080/items" , { signal })
        .then((res) => {
            return res.json()})
        .then(({items}) => {
            dispatch(fetchStatusAction.markFetchingFinished())
            dispatch(fetchStatusAction.markFetchDone())
            dispatch(itemsAction.addInitialItems(items[0]))
        });
        return () => controller.abort();
        }, [fetchStatus]
    );
    
    return (
        <></>
    )
}

export default FetchItems;