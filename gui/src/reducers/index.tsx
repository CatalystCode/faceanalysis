import { ActionWithPayload, ADD_IMAGE, ImageProperties,  } from '../constants';


const initialState = {
  images : Array<ImageProperties>()
};
const rootReducer = (state = initialState, action: ActionWithPayload<ImageProperties>  ) => {
  switch (action.type){
    case ADD_IMAGE:
      state.images.push(action.payload);
      return state;
    default:
      return state;
  }
};

export default rootReducer;