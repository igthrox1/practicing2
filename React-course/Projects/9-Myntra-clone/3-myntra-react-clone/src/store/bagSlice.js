import { createSlice } from "@reduxjs/toolkit";

const BagSlice = createSlice({
  name: "bag",
  initialState: [],
  reducers: {
    addTobag: (state, actions) => {
      state.push(actions.payload);
    },
    removeFromBag: (state, actions) => {
      return state.filter(itemId => itemId !== actions.payload);
    }
  },
});
 
export const bagAction = BagSlice.actions;

export default BagSlice;
