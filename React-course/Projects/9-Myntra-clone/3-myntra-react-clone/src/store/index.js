import { configureStore } from '@reduxjs/toolkit'
import itemSlice from './itemSlice';
import fetchStatusSlice from './fetchStatusSlice';
import BagSlice from './bagSlice';

const MyntraStore = configureStore({
    reducer : {
        items : itemSlice.reducer,
        fetchStatus:fetchStatusSlice.reducer,
        bag:BagSlice.reducer
    }
})

export default MyntraStore;